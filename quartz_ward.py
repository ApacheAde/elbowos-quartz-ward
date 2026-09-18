#!/usr/bin/env python3
"""QUARTZ WARD — neon tower-lite arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/QUARTZ_WARD_ElbowOS.mp4")
TITLE, HANDLE = "QUARTZ WARD", "x.com/ElbowOS"

INK = (4, 14, 18)
MOSS = (8, 38, 34)
JADE = (18, 72, 58)
MINT = (110, 255, 186)
ROSE = (255, 72, 128)
CORAL = (255, 110, 78)
GOLD = (255, 206, 86)
AMBER = (255, 158, 52)
ICE = (140, 220, 255)
WHITE = (246, 250, 255)
VIO = (168, 92, 255)


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("DejaVu Sans", 56, bold=True)
        self.font = pygame.font.SysFont("DejaVu Sans", 34, bold=True)
        self.font_sm = pygame.font.SysFont("DejaVu Sans", 24)
        self.clock = pygame.time.Clock()
        self.lanes = 3
        self.lane_x = [270, 540, 810]
        self.core_y = 1580
        self.reset()

    def reset(self):
        self.t = self.score = self.combo = self.flash = self.banner = 0
        self.banner_txt = ""
        self.wave = 1
        self.hp = 8
        self.lane = 1
        self.aim = 1
        self.cool = 0
        self.bugs, self.bolts, self.sparks, self.motes = [], [], [], []
        for _ in range(80):
            self.motes.append([random.randrange(W), random.randrange(H),
                               random.uniform(0.3, 1.6), random.choice((JADE, ICE, VIO))])

    def spawn(self):
        rate = max(10, 28 - self.wave * 2)
        if self.t % rate == 0:
            li = random.randrange(self.lanes)
            kind = "wasp" if random.random() < 0.35 else "scarab"
            hp = 2 if kind == "wasp" else 1
            spd = random.uniform(4.2, 6.4) + self.wave * 0.35
            if kind == "wasp":
                spd += 1.4
            self.bugs.append([self.lane_x[li], -40, li, spd, hp, kind, random.random() * 6.28])

    def fire(self, li=None):
        if self.cool > 0:
            return
        li = self.lane if li is None else li
        x = self.lane_x[li]
        self.bolts.append([x, self.core_y - 90, -22])
        self.cool = 5
        self.burst(x, self.core_y - 70, MINT, 6)

    def burst(self, x, y, col, n=12):
        for _ in range(n):
            a = random.uniform(0, 6.2832)
            sp = random.uniform(1.6, 9)
            self.sparks.append([x, y, math.cos(a) * sp, math.sin(a) * sp, 16, col])

    def autoplay(self):
        lowest, pick = -1, self.lane
        for b in self.bugs:
            if b[1] > lowest:
                lowest, pick = b[1], b[2]
        self.aim = pick
        if self.lane != self.aim and self.t % 2 == 0:
            self.lane += 1 if self.aim > self.lane else -1
        if self.bugs and self.cool == 0:
            self.fire(self.lane)

    def tick(self):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        self.banner = max(0, self.banner - 1)
        self.cool = max(0, self.cool - 1)
        self.spawn()
        if self.t % 240 == 0:
            self.wave += 1
            self.banner, self.banner_txt = 28, f"WAVE {self.wave}"
        for m in self.motes:
            m[1] += m[2]
            if m[1] > H:
                m[0], m[1] = random.randrange(W), -10
        for b in self.bugs:
            wob = math.sin(self.t * 0.18 + b[6]) * (10 if b[5] == "wasp" else 3)
            b[0] = self.lane_x[b[2]] + wob
            b[1] += b[3]
        for bolt in self.bolts:
            bolt[1] += bolt[2]
        hits = []
        for i, bolt in enumerate(self.bolts):
            for j, bug in enumerate(self.bugs):
                if abs(bolt[0] - bug[0]) < 42 and abs(bolt[1] - bug[1]) < 40:
                    bug[4] -= 1
                    hits.append(i)
                    self.burst(bug[0], bug[1], MINT, 8)
                    if bug[4] <= 0:
                        pts = 40 if bug[5] == "wasp" else 20
                        self.combo += 1
                        self.score += pts + self.combo * 4
                        self.burst(bug[0], bug[1], GOLD if bug[5] == "wasp" else ROSE, 18)
                        bug[1] = 9999
                    break
        self.bolts = [b for k, b in enumerate(self.bolts) if k not in hits and b[1] > -40]
        leaked = []
        for bug in self.bugs:
            if bug[1] >= self.core_y - 20:
                leaked.append(bug)
                self.hp -= 1
                self.combo = 0
                self.flash = 8
                self.burst(bug[0], self.core_y, CORAL, 20)
        self.bugs = [b for b in self.bugs if b[1] < self.core_y - 20]
        if self.hp <= 0:
            self.banner, self.banner_txt = 40, "RESHARD"
            self.hp = 8
            self.wave = max(1, self.wave - 1)
            self.bugs.clear()
        for sp in self.sparks:
            sp[0] += sp[2]
            sp[1] += sp[3]
            sp[4] -= 1
        self.sparks = [s for s in self.sparks if s[4] > 0]

    def draw_ward(self, surf):
        x, y = self.lane_x[self.lane], self.core_y
        pygame.draw.polygon(surf, AMBER, [(x, y - 110), (x + 70, y - 20), (x + 40, y + 50),
                                          (x - 40, y + 50), (x - 70, y - 20)])
        pygame.draw.polygon(surf, GOLD, [(x, y - 92), (x + 42, y - 18), (x, y + 28), (x - 42, y - 18)])
        pygame.draw.circle(surf, WHITE, (x, y - 18), 16)
        pulse = 18 + int(8 * math.sin(self.t * 0.25))
        pygame.draw.circle(surf, MINT, (x, y - 18), pulse, 3)
        for i, hx in enumerate(self.lane_x):
            col = MINT if i == self.lane else JADE
            pygame.draw.circle(surf, col, (hx, y + 78), 14)

    def draw(self, surf):
        for i in range(24):
            t = i / 23
            pygame.draw.rect(surf, (int(3 + 10 * t), int(12 + 28 * t), int(16 + 22 * (1 - t))),
                             (0, int(i * H / 24), W, H // 24 + 2))
        for m in self.motes:
            pygame.draw.circle(surf, m[3], (int(m[0]), int(m[1])), 3)
        top, bot = 180, self.core_y + 20
        for i, x in enumerate(self.lane_x):
            pygame.draw.line(surf, JADE, (x, top), (x, bot), 6)
            pygame.draw.rect(surf, MOSS, (x - 86, top, 172, bot - top), border_radius=28)
            pygame.draw.rect(surf, JADE, (x - 86, top, 172, bot - top), 2, border_radius=28)
            if i == self.lane:
                glow = pygame.Surface((172, bot - top), pygame.SRCALPHA)
                glow.fill((110, 255, 186, 18))
                surf.blit(glow, (x - 86, top))
        pygame.draw.rect(surf, AMBER, (80, self.core_y + 96, W - 160, 18), border_radius=8)
        hw = int((W - 180) * max(0, self.hp) / 8)
        pygame.draw.rect(surf, ROSE if self.hp < 3 else MINT, (90, self.core_y + 100, hw, 10), border_radius=6)
        self.draw_ward(surf)
        for b in self.bugs:
            x, y = int(b[0]), int(b[1])
            if b[5] == "wasp":
                pygame.draw.ellipse(surf, ICE, (x - 28, y - 18, 56, 36))
                pygame.draw.circle(surf, VIO, (x, y), 16)
                pygame.draw.circle(surf, WHITE, (x - 6, y - 4), 4)
            else:
                pygame.draw.circle(surf, ROSE, (x, y), 26)
                pygame.draw.circle(surf, CORAL, (x, y), 16)
                pygame.draw.circle(surf, GOLD, (x + 6, y - 6), 6)
        for bolt in self.bolts:
            pygame.draw.circle(surf, MINT, (int(bolt[0]), int(bolt[1])), 12)
            pygame.draw.circle(surf, WHITE, (int(bolt[0]), int(bolt[1])), 5)
            pygame.draw.line(surf, MINT, (int(bolt[0]), int(bolt[1])),
                             (int(bolt[0]), int(bolt[1]) + 28), 6)
        for sp in self.sparks:
            pygame.draw.circle(surf, sp[5], (int(sp[0]), int(sp[1])), max(2, sp[4] // 3))
        if self.flash:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 70, 90, 36))
            surf.blit(ov, (0, 0))
        title = self.font_lg.render(TITLE, True, GOLD)
        surf.blit(title, title.get_rect(center=(W // 2, 58)))
        sub = self.font_sm.render(HANDLE, True, MINT)
        surf.blit(sub, sub.get_rect(center=(W // 2, 112)))
        if self.banner:
            lab = self.font.render(self.banner_txt, True, ROSE)
            surf.blit(lab, lab.get_rect(center=(W // 2, 160)))
        sc = self.font.render(f"SCORE  {self.score}", True, WHITE)
        cb = self.font_sm.render(f"COMBO  x{self.combo}    WAVE  {self.wave}    HP  {self.hp}", True, GOLD)
        hint = self.font_sm.render("A / D  shift ward    SPACE  pulse bolt", True, ICE)
        surf.blit(sc, sc.get_rect(center=(W // 2, H - 118)))
        surf.blit(cb, cb.get_rect(center=(W // 2, H - 72)))
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 32)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_LEFT, pygame.K_a):
                        self.lane = max(0, self.lane - 1)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        self.lane = min(self.lanes - 1, self.lane + 1)
                    elif ev.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_w):
                        self.fire()
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    mx, _ = ev.pos
                    self.lane = min(range(self.lanes), key=lambda i: abs(self.lane_x[i] - mx))
                    self.fire()
            self.tick()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay()
                self.tick()
                self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames}", flush=True)
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
