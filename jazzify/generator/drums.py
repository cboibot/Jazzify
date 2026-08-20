"""Section-aware jazz groove with transitions, fills, and an intentional ending."""
KICK, SNARE, CLOSED_HAT, RIDE, CRASH, TOM_LOW, TOM_HIGH = 36, 38, 42, 51, 49, 45, 50


def generate_drums(profile, rng, bars, sections=(), solo_mode=False):
    events = []
    starts = {start for _, start, _ in sections}
    for bar in range(bars):
        section = next(name for name,start,length in sections if start <= bar < start + length)
        activity = 1.0 if solo_mode else profile.drum_activity
        if rng.random() > activity * (.35 if section == "INTRO" else .55 if section == "OUTRO" else 1): continue
        base = bar * 4; cymbal = RIDE if profile.density > .65 else CLOSED_HAT
        positions = (0,1,2,3) if profile.density > .60 else (0,2)
        for beat in positions:
            time = base + beat + (profile.swing * .14 if beat % 2 else 0) + rng.uniform(-profile.humanize, profile.humanize)
            events.append((time,.14,cymbal,rng.randint(profile.velocity_low, max(profile.velocity_low,profile.velocity_high-16))))
        if profile.density > .45:
            for beat in (1,3): events.append((base+beat,.12,SNARE,rng.randint(profile.velocity_low,profile.velocity_high-9)))
        if rng.random() < .45 + profile.syncopation *.35: events.append((base,.14,KICK,rng.randint(profile.velocity_low,profile.velocity_high-6)))
        is_transition = bar + 1 in starts or bar == bars - 1
        if is_transition:
            # The fill signals a form boundary; sparse profiles hear just one soft tom.
            fill_beats = (3.25,3.55,3.75) if profile.density > .55 else (3.5,)
            for index, beat in enumerate(fill_beats): events.append((base+beat,.12,TOM_HIGH if index % 2 else TOM_LOW,rng.randint(profile.velocity_low,profile.velocity_high)))
        if bar in starts and bar and section != "OUTRO": events.append((base,.4,CRASH,profile.velocity_high))
    return events
