from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from .models import RiskProfile
from dashboard.recommendations import get_initial_recommendations_by_risk_profile
from django.http import JsonResponse

QUESTION_SCORE_MAP = {
    'q1-option': {
        'under-30': 5,
        '30-40': 4,
        '40-50': 3,
        '50-60': 2,
        'above-60': 1,
    },
    'q2-option': {
        'no-emergency-fund': 1,
        'less-3-months': 2,
        '4-6-months': 3,
        '7-9-months': 4,
        'more-9-months': 5,
    },
    'q3-option': {
        '0-10-percent': 2,
        '11-20-percent': 3,
        '21-30-percent': 4,
        'more-30-percent': 5,
        'no-income': 1,
    },
    'q4-option': {
        'strongly-agree': 5,
        'agree': 4,
        'neutral': 3,
        'disagree': 2,
        'strongly-disagree': 1,
    },
    'q5-option': {
        '6-percent': 1,
        '10-percent': 2,
        '12-percent': 3,
        '15-percent': 4,
        '20-percent': 5,
    },
    'q6-option': {
        'strongly-agree': 1,
        'agree': 2,
        'neutral': 3,
        'disagree': 4,
        'strongly-disagree': 5,
    },
    'q7-option': {
        'under-2-lakh': 1,
        '2-5-lakh': 2,
        '5-10-lakh': 3,
        '10-20-lakh': 4,
        'more-20-lakh': 5,
    },
    'q8-option': {
        'less-5-percent': 1,
        '5-10-percent': 2,
        '10-20-percent': 3,
        '20-30-percent': 4,
        'more-30-percent': 5,
    },
    'q9-option': {
        'single': 5,
        'couple-without-child': 4,
        'young-family': 3,
        'mature-family': 5,
        'preparing-retirement': 2,
        'retired': 1,
    },
    'q10-option': {
        'not-familiar-uncomfortable': 0,
        'not-familiar': 1,
        'somewhat-familiar': 2,
        'fairly-familiar': 3,
        'very-familiar': 5,
    },
    'q11-option': {
        '2-years-or-less': 1,
        '3-5-years': 3,
        '6-10-years': 4,
        'more-than-10-years': 5,
    },
    'q12-option': {
        'is-not-dependable': 2,
        'is-secure': 5,
        'enough-wealth': 4,
        'some-income': 3,
    },
    'q13-option': {
        'average-out': 5,
        'do-not-bother': 4,
        'book-loss': 1,
        'hold-and-sell': 2,
    },
}

CATEGORY_BOUNDS = [24, 40, 52]


def calculate_risk_category(score):
    if score <= CATEGORY_BOUNDS[0]:
        return 'Conservative'
    if score <= CATEGORY_BOUNDS[1]:
        return 'Balanced'
    if score <= CATEGORY_BOUNDS[2]:
        return 'Assertive'
    return 'Aggressive'


@login_required
def risk_profile(request):
    risk_profile = RiskProfile.objects.filter(user=request.user).first()

    if request.method == 'POST':
        required_fields = [
            'q1-option', 'q2-option', 'q3-option', 'q4-option', 'q5-option',
            'q6-option', 'q7-option', 'q8-option', 'q9-option', 'q10-option',
            'q11-option', 'q12-option', 'q13-option'
        ]

        missing_fields = [field for field in required_fields if not request.POST.get(field)]
        if missing_fields:
            return HttpResponse(
                f'Error: Please complete all questions. Missing: {", ".join(missing_fields)}',
                status=400
            )

        total_score = 0
        answers = {}

        for field in required_fields:
            value = request.POST.get(field)
            answers[field] = value
            total_score += QUESTION_SCORE_MAP.get(field, {}).get(value, 0)

        category = calculate_risk_category(total_score)

        profile_obj = risk_profile if risk_profile else RiskProfile(user=request.user)
        profile_obj.age = answers['q1-option']
        profile_obj.emergency_funds = answers['q2-option']
        profile_obj.investment_percentage = answers['q3-option']
        profile_obj.high_reture_high_risk = answers['q4-option']
        profile_obj.expected_return_rate = answers['q5-option']
        profile_obj.keep_capital_safe = answers['q6-option']
        profile_obj.annual_take_home_income = answers['q7-option']
        profile_obj.worry_if_fall_percentage = answers['q8-option']
        profile_obj.current_life_stage = answers['q9-option']
        profile_obj.investment_familiarity = answers['q10-option']
        profile_obj.investment_length = answers['q11-option']
        profile_obj.work_status = answers['q12-option']
        profile_obj.critical_situation_response = answers['q13-option']
        profile_obj.category = category

        try:
            profile_obj.save()
        except Exception as e:
            return HttpResponse('Error: ' + str(e), status=500)

        # Generate initial recommendations based on risk profile
        recommendations = get_initial_recommendations_by_risk_profile(
            category,
            num_recommendations=10,
            use_ai=True
        )

        context = {
            'risk_profile': profile_obj,
            'risk_category': category,
            'total_score': total_score,
            'recommendations': recommendations,
            'message': f'Based on your {category} risk profile, here are {len(recommendations)} recommended stocks to get you started!'
        }

        return render(request, 'riskprofile/recommendations.html', context)

    return render(request, 'riskprofile/risk-profile.html', {'risk_profile': risk_profile})