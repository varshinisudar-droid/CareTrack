def assess_follow_up(checkins):
    """
    Assess recent patient check-ins and identify
    whether healthcare-provider review may be appropriate.

    The function considers multiple recent check-ins
    to identify persistent monitoring indicators.

    Parameters
    ----------
    checkins : list of dictionaries
        Recent patient check-in records.
        The newest check-in should be first.

    Returns
    -------
    dict
        Follow-up status, score, reasons, and recommendation.
    """

    if not checkins:
        return {
            "status": "Insufficient Data",
            "score": 0,
            "reasons": [
                "No recent check-in data available."
            ],
            "recommendation": (
                "Continue regular monitoring."
            )
        }

    score = 0
    reasons = []

    # Use the most recent 3 check-ins
    recent_checkins = checkins[:3]

    # -------------------------------------------------
    # LATEST CHECK-IN
    # -------------------------------------------------

    latest = recent_checkins[0]

    pain_level = latest.get("pain_level", 0)
    mood = latest.get("mood", 5)
    sleep_hours = latest.get("sleep_hours", 8)
    medication_taken = latest.get(
        "medication_taken",
        True
    )

    # -------------------------------------------------
    # CURRENT PAIN
    # -------------------------------------------------

    if pain_level >= 7:

        score += 2

        reasons.append(
            "High pain level reported in the latest check-in."
        )

    elif pain_level >= 5:

        score += 1

        reasons.append(
            "Moderate pain level reported in the latest check-in."
        )

    # -------------------------------------------------
    # CURRENT MOOD
    # -------------------------------------------------

    if mood <= 2:

        score += 2

        reasons.append(
            "Low mood score reported in the latest check-in."
        )

    elif mood == 3:

        score += 1

        reasons.append(
            "Moderate mood score reported in the latest check-in."
        )

    # -------------------------------------------------
    # CURRENT SLEEP
    # -------------------------------------------------

    if sleep_hours < 5:

        score += 2

        reasons.append(
            "Low sleep duration reported in the latest check-in."
        )

    elif sleep_hours < 6:

        score += 1

        reasons.append(
            "Reduced sleep duration reported in the latest check-in."
        )

    # -------------------------------------------------
    # MEDICATION
    # -------------------------------------------------

    if not medication_taken:

        score += 1

        reasons.append(
            "Medication was reported as not taken."
        )

    # -------------------------------------------------
    # LONGITUDINAL PATTERN
    # -------------------------------------------------

    if len(recent_checkins) >= 2:

        high_pain_count = sum(
            1
            for checkin in recent_checkins
            if checkin.get("pain_level", 0) >= 5
        )

        low_mood_count = sum(
            1
            for checkin in recent_checkins
            if checkin.get("mood", 5) <= 2
        )

        low_sleep_count = sum(
            1
            for checkin in recent_checkins
            if checkin.get("sleep_hours", 8) < 6
        )

        # Persistent pain
        if high_pain_count >= 2:

            score += 2

            reasons.append(
                "Elevated pain has been reported across "
                "multiple recent check-ins."
            )

        # Persistent low mood
        if low_mood_count >= 2:

            score += 2

            reasons.append(
                "Low mood has been reported across "
                "multiple recent check-ins."
            )

        # Persistent reduced sleep
        if low_sleep_count >= 2:

            score += 2

            reasons.append(
                "Reduced sleep has been reported across "
                "multiple recent check-ins."
            )

    # -------------------------------------------------
    # FINAL STATUS
    # -------------------------------------------------

    if score >= 6:

        status = "Review Recommended"

        recommendation = (
            "Multiple monitoring indicators are present "
            "across recent check-ins. Healthcare-provider "
            "review may be appropriate."
        )

    elif score >= 3:

        status = "Monitor Closely"

        recommendation = (
            "Some monitoring indicators are present. "
            "Continue monitoring and consider healthcare-"
            "provider review if the pattern continues."
        )

    else:

        status = "Routine Monitoring"

        recommendation = (
            "No major monitoring indicators were detected "
            "in the recent check-ins."
        )

    return {
        "status": status,
        "score": score,
        "reasons": reasons,
        "recommendation": recommendation
    }