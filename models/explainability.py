def explain_review_attention(checkins):
    """
    Explain the recent check-in factors contributing
    to review attention.

    Academic prototype only.
    """

    if not checkins:
        return []

    recent = checkins[:3]

    explanations = []

    pain_values = [
        checkin.get("pain_level", 0)
        for checkin in recent
    ]

    mood_values = [
        checkin.get("mood", 5)
        for checkin in recent
    ]

    sleep_values = [
        checkin.get("sleep_hours", 8)
        for checkin in recent
    ]

    missed_medications = sum(
        not checkin.get(
            "medication_taken",
            True
        )
        for checkin in recent
    )

    if max(pain_values) >= 5:
        explanations.append(
            "Elevated pain was reported "
            "in recent check-ins."
        )

    if sum(
        mood <= 2
        for mood in mood_values
    ) >= 2:
        explanations.append(
            "Low mood was reported across "
            "multiple recent check-ins."
        )

    if sum(
        sleep < 6
        for sleep in sleep_values
    ) >= 2:
        explanations.append(
            "Reduced sleep was reported across "
            "multiple recent check-ins."
        )

    if missed_medications > 0:
        explanations.append(
            "Medication was reported as missed "
            "in a recent check-in."
        )

    if not explanations:
        explanations.append(
            "No major contributing monitoring "
            "indicators were identified."
        )

    return explanations