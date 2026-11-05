import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ui_theme import safe, card, progress, priorities, tasks


class ThemeTests(unittest.TestCase):
    def test_user_values_escaped(self):
        result=card('<script>alert(1)</script>',10,'ok')
        self.assertNotIn('<script>',result)
        self.assertIn('&lt;script&gt;',result)

    def test_weekly_progress_over_target_clamped(self):
        view=progress('Semana',3000,1500)
        self.assertIn('width:100.0%',view)
        self.assertNotIn('width:200.0%',view)

    def test_priorities_without_questions_do_not_fake_performance(self):
        row={'disciplina':'Contabilidade Geral','prioridade':18.0,'rendimento':None,'questoes':0}
        out=priorities([row], lambda x:'—')
        self.assertIn('Aguardando diagnóstico',out)

    def test_task_html_escaped(self):
        result=tasks([{'day':'2026-11-05','subject':'<b>X</b>','topic':'assunto','method':'Teoria','target_minutes':40}])
        self.assertNotIn('<b>X</b>',result)
        self.assertIn('&lt;b&gt;X&lt;/b&gt;',result)

if __name__=='__main__':unittest.main()