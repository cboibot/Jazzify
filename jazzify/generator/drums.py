KICK, SNARE, CLOSED_HAT, RIDE, CRASH = 36, 38, 42, 51, 49

def generate_drums(profile, rng, bars, section_starts=()):
    events = []
    for bar in range(bars):
        if rng.random() > profile.drum_activity: continue
        base = bar * 4
        # Ballads and dark jazz use a quiet hat pulse, while bebop rides constantly.
        cymbal = RIDE if profile.density > .65 else CLOSED_HAT
        positions = (0,1,2,3) if profile.density > .64 else (0,2)
        for beat in positions: events.append((base + beat, .16, cymbal, rng.randint(profile.velocity_low, profile.velocity_high - 15)))
        if profile.density > .48:
            for beat in (1,3): events.append((base + beat, .12, SNARE, rng.randint(profile.velocity_low, profile.velocity_high - 8)))
        if rng.random() < (.50 + profile.syncopation * .35): events.append((base, .15, KICK, rng.randint(profile.velocity_low, profile.velocity_high - 6)))
        if rng.random() < profile.syncopation: events.append((base + rng.choice((.5,1.5,2.5,3.5)), .12, KICK, profile.velocity_low + 6))
        if bar in section_starts and bar != 0: events.append((base, .45, CRASH, profile.velocity_high))
    return events
