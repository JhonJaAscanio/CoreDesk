"""Pruebas de la migración de datos desde el nombre anterior del proyecto (Autorizador).

Ejecutar desde la raíz del proyecto:  py -3.11 -m unittest discover -s tests -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QByteArray, QSettings  # noqa: E402

import CoreDesk  # noqa: E402


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="coredesk_test_")
        # Instalación anterior simulada: <root>\Organizacion\Autorizador\perfil
        self.legacy_dir = os.path.join(self.root, "Organizacion", "Autorizador")
        os.makedirs(os.path.join(self.legacy_dir, "perfil", "Local Storage"))
        self.write(os.path.join(self.legacy_dir, "perfil", "Cookies"), "cookies")
        self.write(os.path.join(self.legacy_dir, "perfil", "Local Storage", "datos"), "almacenamiento")
        self.new_dir = os.path.join(self.root, "CoreDesk")
        os.makedirs(self.new_dir)

        self.legacy_settings = QSettings(os.path.join(self.root, "anterior.ini"), QSettings.Format.IniFormat)
        self.legacy_settings.setValue("history", ["https://example.com/", "https://example.org/"])
        self.legacy_settings.setValue("session", ["https://example.com/"])
        self.legacy_settings.setValue("geometry", QByteArray(b"\x01\x02geometria"))
        self.legacy_settings.sync()
        self.settings = QSettings(os.path.join(self.root, "nuevo.ini"), QSettings.Format.IniFormat)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    @staticmethod
    def write(path, text):
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)

    @staticmethod
    def read(path):
        with open(path, encoding="utf-8") as file:
            return file.read()

    def migrate(self):
        return CoreDesk.migrate_legacy_data(self.new_dir, self.settings, self.legacy_dir, self.legacy_settings)

    def test_finds_legacy_data_dir(self):
        self.assertEqual(CoreDesk.find_legacy_data_dir(self.root), self.legacy_dir)

    def test_no_legacy_data_dir(self):
        empty = tempfile.mkdtemp(prefix="coredesk_vacio_")
        try:
            self.assertIsNone(CoreDesk.find_legacy_data_dir(empty))
        finally:
            shutil.rmtree(empty)

    def test_copies_profile_and_settings(self):
        self.assertIsNone(self.migrate())
        self.assertEqual(self.read(os.path.join(self.new_dir, "perfil", "Cookies")), "cookies")
        self.assertEqual(self.read(os.path.join(self.new_dir, "perfil", "Local Storage", "datos")), "almacenamiento")
        self.assertEqual(self.settings.value("history", type=list), ["https://example.com/", "https://example.org/"])
        self.assertEqual(self.settings.value("session", type=list), ["https://example.com/"])
        self.assertEqual(bytes(self.settings.value("geometry")), b"\x01\x02geometria")

    def test_originals_are_not_modified(self):
        self.migrate()
        self.assertEqual(self.read(os.path.join(self.legacy_dir, "perfil", "Cookies")), "cookies")
        self.assertEqual(self.legacy_settings.value("history", type=list),
                         ["https://example.com/", "https://example.org/"])

    def test_writes_backup_and_marker(self):
        self.migrate()
        with open(os.path.join(self.new_dir, "respaldo_migracion", "preferencias_anteriores.json"), encoding="utf-8") as f:
            backup = json.load(f)
        self.assertEqual(backup["session"], ["https://example.com/"])
        self.assertIn("geometry", backup)
        with open(os.path.join(self.new_dir, CoreDesk.MIGRATION_MARKER), encoding="utf-8") as f:
            marker = json.load(f)
        self.assertEqual(marker["perfil"], "copiado")
        self.assertEqual(marker["preferencias"], ["geometry", "history", "session"])

    def test_runs_only_once(self):
        self.migrate()
        self.settings.setValue("history", ["https://nuevo.example/"])
        self.write(os.path.join(self.new_dir, "perfil", "Cookies"), "cookies nuevas")
        self.assertIsNone(self.migrate())
        self.assertEqual(self.settings.value("history", type=list), ["https://nuevo.example/"])
        self.assertEqual(self.read(os.path.join(self.new_dir, "perfil", "Cookies")), "cookies nuevas")

    def test_does_not_overwrite_existing_new_data(self):
        os.makedirs(os.path.join(self.new_dir, "perfil"))
        self.write(os.path.join(self.new_dir, "perfil", "Cookies"), "propias")
        self.settings.setValue("session", ["https://propia.example/"])
        self.assertIsNone(self.migrate())
        self.assertEqual(self.read(os.path.join(self.new_dir, "perfil", "Cookies")), "propias")
        self.assertEqual(self.settings.value("session", type=list), ["https://propia.example/"])

    def test_copy_failure_leaves_no_partial_copy_and_retries(self):
        def failing_copy(source, destination):
            os.makedirs(destination)
            raise shutil.Error([("Cookies", "Cookies", "archivo en uso")])

        with mock.patch.object(CoreDesk.shutil, "copytree", side_effect=failing_copy):
            message = self.migrate()
        self.assertIn("Cierra todas las ventanas", message)
        self.assertFalse(os.path.exists(os.path.join(self.new_dir, "perfil")))
        self.assertFalse(os.path.exists(os.path.join(self.new_dir, "perfil.migrando")))
        self.assertFalse(os.path.exists(os.path.join(self.new_dir, CoreDesk.MIGRATION_MARKER)))
        # El siguiente arranque vuelve a intentarlo y completa la copia
        self.assertIsNone(self.migrate())
        self.assertEqual(self.read(os.path.join(self.new_dir, "perfil", "Cookies")), "cookies")

    def test_without_previous_installation(self):
        result = CoreDesk.migrate_legacy_data(self.new_dir, self.settings, None, None)
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(os.path.join(self.new_dir, "perfil")))
        self.assertTrue(os.path.exists(os.path.join(self.new_dir, CoreDesk.MIGRATION_MARKER)))


if __name__ == "__main__":
    unittest.main()
