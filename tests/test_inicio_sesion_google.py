"""Pruebas del aviso de inicio de sesión de Google y de abrir la página en el navegador predeterminado.

Ejecutar desde la raíz del proyecto:  py -3.11 -m unittest discover -s tests -v
"""
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QEventLoop, QSettings, QTimer, QUrl  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

import CoreDesk  # noqa: E402

REJECTED = "https://accounts.google.com/v3/signin/rejected?continue=https%3A%2F%2Fmail.google.com"
SIGNIN = "https://accounts.google.com/v3/signin/identifier?continue=https%3A%2F%2Fmail.google.com"


class GoogleSigninStateTest(unittest.TestCase):
    def test_states(self):
        self.assertEqual(CoreDesk.google_signin_state(QUrl(REJECTED)), "rechazado")
        self.assertEqual(CoreDesk.google_signin_state(QUrl(SIGNIN)), "inicio")
        self.assertEqual(CoreDesk.google_signin_state(QUrl("https://accounts.google.com/ServiceLogin")), "inicio")
        self.assertIsNone(CoreDesk.google_signin_state(QUrl("https://mail.google.com/mail/u/1/")))
        self.assertIsNone(CoreDesk.google_signin_state(QUrl("https://example.com/signin/rejected")))


class InfoBarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.root = tempfile.mkdtemp(prefix="coredesk_google_")
        cls.settings_patch = mock.patch.object(
            CoreDesk, "app_settings", lambda: QSettings(os.path.join(cls.root, "t.ini"), QSettings.Format.IniFormat))
        cls.settings_patch.start()
        # Nunca se abre el navegador real durante las pruebas
        cls.browser_patch = mock.patch.object(CoreDesk.QDesktopServices, "openUrl", return_value=True)
        cls.open_url = cls.browser_patch.start()
        cls.profile = CoreDesk.create_profile()
        cls.profile.setPersistentStoragePath(os.path.join(cls.root, "perfil"))
        cls.profile.setCachePath(os.path.join(cls.root, "cache"))
        cls.window = CoreDesk.MainWindow(cls.profile)
        cls.window.show()

    @classmethod
    def tearDownClass(cls):
        cls.window.close()
        del cls.window
        cls.settings_patch.stop()
        cls.browser_patch.stop()
        shutil.rmtree(cls.root, ignore_errors=True)

    @staticmethod
    def wait(ms):
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()

    def setUp(self):
        self.open_url.reset_mock()

    def show_page(self, url):
        view = self.window.current_view()
        view.setHtml("<p>prueba</p>", QUrl(url))
        self.wait(1500)
        return view

    def test_rejection_opens_browser_and_goes_back(self):
        view = self.show_page("https://example.com/antes")
        self.show_page(SIGNIN)
        self.show_page(REJECTED)
        self.open_url.assert_called_once()
        self.assertEqual(self.open_url.call_args[0][0].toString(), "https://mail.google.com")
        self.assertEqual(view.url().toString(), SIGNIN)

    def test_rejection_opens_browser_only_once_per_signin(self):
        self.show_page("https://example.com/antes")
        self.show_page(SIGNIN)
        self.show_page(REJECTED)
        # Al volver, Google puede redirigir otra vez al rechazo: no se abre el navegador en bucle
        self.show_page(REJECTED)
        self.assertEqual(self.open_url.call_count, 1)
        # Tras salir de Google, un nuevo rechazo vuelve a abrir el navegador
        self.show_page("https://example.com/despues")
        self.show_page(REJECTED)
        self.assertEqual(self.open_url.call_count, 2)

    def test_signin_page_shows_hint_and_can_be_dismissed(self):
        self.show_page(SIGNIN)
        self.assertTrue(self.window.info_bar.isVisible())
        self.assertEqual(self.window.info_bar.property("state"), "inicio")
        self.window.dismiss_info_bar()
        self.assertFalse(self.window.info_bar.isVisible())
        # Al salir de Google se reinicia
        self.show_page("https://example.com/")
        self.show_page(SIGNIN)
        self.assertTrue(self.window.info_bar.isVisible())

    def test_other_pages_hide_info_bar(self):
        self.show_page("https://example.com/")
        self.assertFalse(self.window.info_bar.isVisible())

    def open_in_browser_url(self, url):
        self.show_page(url)
        self.open_url.reset_mock()
        self.window.open_in_browser()
        self.open_url.assert_called_once()
        return self.open_url.call_args[0][0].toString()

    def test_open_in_browser_uses_same_url(self):
        self.assertEqual(self.open_in_browser_url("https://example.com/pagina?a=1"), "https://example.com/pagina?a=1")

    def test_open_in_browser_restarts_google_signin_at_destination(self):
        self.assertEqual(self.open_in_browser_url(SIGNIN), "https://mail.google.com")

    def test_open_in_browser_google_signin_without_destination(self):
        self.assertEqual(self.open_in_browser_url("https://accounts.google.com/v3/signin/challenge/pk"),
                         "https://accounts.google.com/")

    def test_open_in_browser_ignores_local_pages(self):
        self.window.current_view().setHtml("<p>inicio</p>")
        self.wait(800)
        self.window.open_in_browser()
        self.open_url.assert_not_called()


if __name__ == "__main__":
    unittest.main()
