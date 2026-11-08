"""Regressões estáticas de marca e animação: sem browser e sem dados privados."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class HeroBrandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "web/app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "web/style.css").read_text(encoding="utf-8")
        cls.scene = (ROOT / "web/modules/hero_duel.js").read_text(encoding="utf-8")
        cls.intro = (ROOT / "web/modules/intro.js").read_text(encoding="utf-8")

    def test_metallic_wordmark_on_hero(self):
        self.assertIn('class="metal-word metal-silver">CONTROLE', self.app)
        self.assertIn('class="metal-word metal-gold">MESTRE', self.app)
        self.assertIn(".hero-title .metal-silver", self.css)
        self.assertIn(".hero-title .metal-gold", self.css)

    def test_official_quote_remains_visible(self):
        self.assertIn("O PODER NÃO ESTÁ NA PEÇA.", self.app)
        self.assertIn("ESTÁ NA ESTRATÉGIA DE QUEM A MOVE.", self.app)
        self.assertIn('class="hero-motto"', self.app)

    def test_chess_duel_is_inside_existing_parallax_layer(self):
        hero = self.app.split("function heroBanner(d){", 1)[1].split("\nfunction overviewView(d)", 1)[0]
        self.assertEqual(hero.count('class="parallax-layer '), 5)
        self.assertIn('heroDuelMarkup(introVisible)', hero)
        self.assertIn('class="parallax-layer layer-chess-scene"', hero)
        self.assertIn("hero-duel-pawn", self.scene)
        self.assertIn("hero-duel-king", self.scene)

    def test_chess_duel_waits_for_intro_and_respects_reduced_motion(self):
        self.assertIn("cm:intro:finished", self.intro)
        self.assertIn("cm:intro:finished", self.app)
        self.assertIn("classList.add('is-playing')", self.app)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)
        self.assertIn(".hero-duel-stage .hero-duel-king{animation:none!important", self.css)

    def test_motion_is_css_and_no_remote_assets_required(self):
        self.assertIn("@keyframes cm-hero-pawn", self.css)
        self.assertIn("@keyframes cm-hero-king", self.css)
        self.assertIn("@keyframes cm-hero-hit", self.css)
        self.assertNotIn("https://", self.scene)
        self.assertNotIn("<script", self.scene)

    def test_launcher_targets_the_new_build(self):
        launch = (ROOT / "launch.py").read_text(encoding="utf-8")
        server = (ROOT / "web_server.py").read_text(encoding="utf-8")
        self.assertIn("info.get('build') == 'hero-duel-metal-1'", launch)
        self.assertIn("'build':'hero-duel-metal-1'", server)

    def test_svg_wordmarks_are_valid_and_metallic(self):
        for name in ("logo_horizontal_premium.svg", "logo_vertical_premium.svg", "logo_sidebar.svg"):
            with self.subTest(asset=name):
                tree = ET.parse(ROOT / "web/assets/branding" / name)
                root = tree.getroot()
                svg_ns = "{http://www.w3.org/2000/svg}"
                defs = [x.get("id") for x in root.iter() if x.tag == svg_ns + "linearGradient"]
                self.assertIn("cm-silver-word", defs)
                self.assertIn("cm-gold-word", defs)
                wordmarks = {("".join(x.itertext())).strip(): x.get("fill")
                             for x in root.iter() if x.tag == svg_ns + "text"}
                self.assertEqual(wordmarks["CONTROLE"], "url(#cm-silver-word)")
                self.assertEqual(wordmarks["MESTRE"], "url(#cm-gold-word)")


if __name__ == "__main__":
    unittest.main()
