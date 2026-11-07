"""Testes do inicializador local, sem abrir interface real nem alterar estudos."""
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import launch


class LaunchTests(unittest.TestCase):
    def test_essential_files_present(self):
        self.assertFalse([p for p in launch.ESSENTIAL if not (launch.ROOT / p).is_file()])

    def test_reserved_ankiconnect_port_never_selected(self):
        self.assertNotIn(8765,launch.PORTS)
        self.assertEqual(launch.PORTS[0],8771)
        self.assertIn('sources.py',launch.ESSENTIAL)

    def test_select_free_port(self):
        with patch.object(launch, 'PORTS', (18761,)), \
             patch.object(launch, '_existing_controle_mestre', return_value=False), \
             patch.object(launch, '_port_is_available', return_value=True):
            self.assertEqual(launch.select_port(), (18761, False))

    def test_existing_instance_wins(self):
        with patch.object(launch, 'PORTS', (18761,)), \
             patch.object(launch, '_existing_controle_mestre', return_value=True):
            self.assertEqual(launch.select_port(), (18761, True))

    def test_occupied_port_skipped(self):
        with patch.object(launch, 'PORTS', (18761, 18762)), \
             patch.object(launch, '_existing_controle_mestre', return_value=False), \
             patch.object(launch, '_port_is_available', side_effect=(False, True)):
            self.assertEqual(launch.select_port(), (18762, False))

    def test_no_available_port(self):
        with patch.object(launch, 'PORTS', (18761,)), \
             patch.object(launch, '_existing_controle_mestre', return_value=False), \
             patch.object(launch, '_port_is_available', return_value=False):
            with self.assertRaises(RuntimeError):
                launch.select_port()

if __name__ == '__main__':
    unittest.main()