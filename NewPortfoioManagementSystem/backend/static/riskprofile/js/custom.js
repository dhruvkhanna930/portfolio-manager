
$(document).ready(function() {
	'use strict';

  $('.test-step .button').on('click', function(e) {
  	e.preventDefault();
    $(this).parents('.test-step').next().addClass('active');
    $(this).parents('.test-step').removeClass('active');
  })

  $('.test-step .prev-btn').on('click', function(e) {
    e.preventDefault();
    $(this).parents('.test-step').prev().addClass('active');
    $(this).parents('.test-step').removeClass('active');
  })

  // Handle form submission
  $('form').on('submit', function(e) {
    // Get all required field names
    const requiredFields = [
      'q1-option', 'q2-option', 'q3-option', 'q4-option', 'q5-option',
      'q6-option', 'q7-option', 'q8-option', 'q9-option', 'q10-option',
      'q11-option', 'q12-option', 'q13-option'
    ];

    let allFieldsSelected = true;
    let missingFields = [];

    // Check each required field
    requiredFields.forEach(function(fieldName) {
      const selectedValue = $('input[name="' + fieldName + '"]:checked').val();
      if (!selectedValue) {
        allFieldsSelected = false;
        missingFields.push(fieldName);
      }
    });

    if (!allFieldsSelected) {
      e.preventDefault();
      alert('Please answer all questions before submitting. Missing answers for: ' + missingFields.join(', '));
      return false;
    }

    // If all fields are selected, allow form submission
    return true;
  });

  // Optional: Add cursor:pointer to submit button
  $('.submit-button').css('cursor', 'pointer');

})
