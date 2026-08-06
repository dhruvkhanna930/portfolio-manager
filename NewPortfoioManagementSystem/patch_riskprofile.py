from pathlib import Path
import re

base_paths = [
    Path('frontend/templates/riskprofile/risk-profile.html'),
    Path('backend/templates/riskprofile/risk-profile.html')
]
field_map = {
    'q1-option': 'age',
    'q2-option': 'emergency_funds',
    'q3-option': 'investment_percentage',
    'q4-option': 'high_reture_high_risk',
    'q5-option': 'expected_return_rate',
    'q6-option': 'keep_capital_safe',
    'q7-option': 'annual_take_home_income',
    'q8-option': 'worry_if_fall_percentage',
    'q9-option': 'current_life_stage',
    'q10-option': 'investment_familiarity',
    'q11-option': 'investment_length',
    'q12-option': 'work_status',
    'q13-option': 'critical_situation_response',
}
fix_values = {
    'q5-option': {'more-15-percent': '20-percent'},
    'q7-option': {'over-20-lakh': 'more-20-lakh'},
    'q11-option': {'10-plus-years': 'more-than-10-years'},
    'q12-option': {'change-career': 'some-income'},
}
pattern = re.compile(r'(<input[^>]*name="(q[0-9]+-option)"[^>]*value="([^"]+)"[^>]*>)')

for path in base_paths:
    if not path.exists():
        continue
    text = path.read_text(encoding='utf-8')
    text = text.replace(
        '{% csrf_token %}',
        '{% csrf_token %}\n                {% if error %}\n                  <div class="alert alert-danger" role="alert">{{ error }}</div>\n                {% endif %}'
    )

    def repl(match):
        tag = match.group(1)
        name = match.group(2)
        value = match.group(3)
        if name in fix_values and value in fix_values[name]:
            new_value = fix_values[name][value]
            tag = tag.replace(f'value="{value}"', f'value="{new_value}"')
            tag = tag.replace(f'id="{value}"', f'id="{new_value}"')
            value = new_value
        if 'checked' not in tag:
            tag = tag[:-1] + f' {{% if risk_profile and risk_profile.{field_map[name]} == "{value}" %}}checked{{% endif %}}>'
        return tag

    text = pattern.sub(repl, text)
    text = text.replace('id="change-career" value="change-career"', 'id="some-income" value="some-income"')
    path.write_text(text, encoding='utf-8')
    print('updated', path)
