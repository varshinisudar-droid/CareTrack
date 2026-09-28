import sys
import os

# Add CareTrack project folder to Python path
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from models.follow_up_logic import assess_follow_up


# =========================================================
# TEST FUNCTION
# =========================================================

def run_test(
    test_name,
    checkins,
    expected_status
):

    result = assess_follow_up(
        checkins
    )

    actual_status = result["status"]

    if actual_status == expected_status:

        print(
            f"PASS: {test_name}"
        )

    else:

        print(
            f"FAIL: {test_name}"
        )

        print(
            f"Expected: {expected_status}"
        )

        print(
            f"Got: {actual_status}"
        )

        print(
            f"Score: {result['score']}"
        )

        print(
            f"Reasons: {result['reasons']}"
        )


# =========================================================
# TEST 1
# NORMAL MONITORING
# =========================================================

normal_checkins = [

    {
        "pain_level": 2,
        "mood": 4,
        "sleep_hours": 8,
        "medication_taken": True
    },

    {
        "pain_level": 2,
        "mood": 4,
        "sleep_hours": 8,
        "medication_taken": True
    },

    {
        "pain_level": 1,
        "mood": 5,
        "sleep_hours": 8,
        "medication_taken": True
    }

]

run_test(
    "Normal check-ins",
    normal_checkins,
    "Routine Monitoring"
)


# =========================================================
# TEST 2
# MODERATE INDICATORS
# =========================================================

moderate_checkins = [

    {
        "pain_level": 5,
        "mood": 3,
        "sleep_hours": 6,
        "medication_taken": True
    },

    {
        "pain_level": 3,
        "mood": 4,
        "sleep_hours": 7,
        "medication_taken": True
    },

    {
        "pain_level": 2,
        "mood": 4,
        "sleep_hours": 7,
        "medication_taken": True
    }

]

run_test(
    "Moderate indicators",
    moderate_checkins,
    "Routine Monitoring"
)


# =========================================================
# TEST 3
# MULTIPLE HIGH INDICATORS
# =========================================================

high_attention_checkins = [

    {
        "pain_level": 8,
        "mood": 2,
        "sleep_hours": 4,
        "medication_taken": False
    },

    {
        "pain_level": 7,
        "mood": 2,
        "sleep_hours": 5,
        "medication_taken": False
    },

    {
        "pain_level": 7,
        "mood": 1,
        "sleep_hours": 4,
        "medication_taken": True
    }

]

run_test(
    "Multiple high indicators",
    high_attention_checkins,
    "Review Recommended"
)


# =========================================================
# TEST 4
# NO DATA
# =========================================================

run_test(
    "No check-in data",
    [],
    "Insufficient Data"
)


# =========================================================
# TEST 5
# SINGLE CHECK-IN WITH HIGH PAIN
# =========================================================

high_pain_checkin = [

    {
        "pain_level": 8,
        "mood": 4,
        "sleep_hours": 7,
        "medication_taken": True
    }

]

run_test(
    "Single high pain check-in",
    high_pain_checkin,
    "Routine Monitoring"
)


# =========================================================
# TEST 6
# MISSED MEDICATION
# =========================================================

missed_medication_checkin = [

    {
        "pain_level": 2,
        "mood": 4,
        "sleep_hours": 8,
        "medication_taken": False
    }

]

run_test(
    "Missed medication",
    missed_medication_checkin,
    "Routine Monitoring"
)


# =========================================================
# TEST 7
# PERSISTENT PAIN
# =========================================================

persistent_pain_checkins = [

    {
        "pain_level": 6,
        "mood": 4,
        "sleep_hours": 7,
        "medication_taken": True
    },

    {
        "pain_level": 6,
        "mood": 4,
        "sleep_hours": 7,
        "medication_taken": True
    },

    {
        "pain_level": 5,
        "mood": 4,
        "sleep_hours": 7,
        "medication_taken": True
    }

]

run_test(
    "Persistent pain",
    persistent_pain_checkins,
    "Monitor Closely"
)


# =========================================================
# TEST 8
# PERSISTENT LOW MOOD
# =========================================================

persistent_low_mood = [

    {
        "pain_level": 2,
        "mood": 2,
        "sleep_hours": 7,
        "medication_taken": True
    },

    {
        "pain_level": 2,
        "mood": 2,
        "sleep_hours": 7,
        "medication_taken": True
    },

    {
        "pain_level": 2,
        "mood": 1,
        "sleep_hours": 7,
        "medication_taken": True
    }

]

run_test(
    "Persistent low mood",
    persistent_low_mood,
    "Monitor Closely"
)


# =========================================================
# TEST 9
# PERSISTENT LOW SLEEP
# =========================================================

persistent_low_sleep = [

    {
        "pain_level": 2,
        "mood": 4,
        "sleep_hours": 5,
        "medication_taken": True
    },

    {
        "pain_level": 2,
        "mood": 4,
        "sleep_hours": 5,
        "medication_taken": True
    },

    {
        "pain_level": 2,
        "mood": 4,
        "sleep_hours": 5,
        "medication_taken": True
    }

]

run_test(
    "Persistent low sleep",
    persistent_low_sleep,
    "Monitor Closely"
)


# =========================================================
# FINISHED
# =========================================================

print(
    "\nFollow-up testing completed."
)