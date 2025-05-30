/*
A java script file that includes all the java-script scripts of the project
The 3 main functions are
1. Set input on the kids
  - Sets the number of kids
  - Sets the kids ages - sets the ages of each kid.
2. Trip location - using auto complete to help the user with finding the right place like Country, state, region or city. Power by google-maps API
3. Sets the trip dates - using a nice display to show the calendar and allow the user to select the trip dates

*/



/*
The user selects the number of kids in this trip and their ages
I used GPT for this code
*/
let numKids = 0;

/* the user can add more kids to the trip - from 0 to 9 */
function increaseKids() {
  if (numKids < 9) {
      numKids++;
      updateKidsDisplay();
      generateAgeFields();
  }
}

/* the user can reduce the number of kids in this trip */
function decreaseKids() {
  if (numKids > 0) {
      numKids--;
      updateKidsDisplay();
      generateAgeFields();
  }
}
/* display the number of kids */
function updateKidsDisplay() {
  document.getElementById('numKidsDisplay').innerText = numKids;
  document.getElementById('children_amount').value = numKids;
}

/* write the kids ages as hover */
function generateAgeFields() {
  const ageFieldsContainer = document.getElementById('ageFieldsContainer');


  ageFieldsContainer.innerHTML = '';


  for (let i = 1; i <= numKids; i++) {
      const ageFieldDiv = document.createElement('div');
      ageFieldDiv.classList.add('input-container');

      const label = document.createElement('label');
      label.setAttribute('for', `kidAge${i}`);
      label.innerText = `Age ${i}: `;

      const select = document.createElement('select');
      select.id = `kidAge${i}`;
      select.name = `kidAge${i}`;
      select.required = true;
      select.style.width = '150px';

      for (let age = 0; age <= 21; age++) {
        const option = document.createElement('option');
        option.value = age.toString();
        option.innerText = `${age}`;
        select.appendChild(option);
      }

      ageFieldDiv.appendChild(label);
      ageFieldDiv.appendChild(select);
      ageFieldsContainer.appendChild(ageFieldDiv);
  }
}/*
The user can select the dates of the trip
I took this part from the web (GPT advise)
*/
flatpickr("#datePicker", {
  dateFormat: "m-d",  /* the display is month and day without the year (to reduce consumed space) */
  minDate: "today", /* cant go to trips in the past*/
  mode: "range" /* range of dates */
});

/* I took this part from Finance
Validates the the code is OK  */

document.addEventListener('DOMContentLoaded', function() {
  const html = '<!DOCTYPE ' +
  document.doctype.name +
  (document.doctype.publicId ? ' PUBLIC "' + document.doctype.publicId + '"' : '') +
  (!document.doctype.publicId && document.doctype.systemId ? ' SYSTEM' : '') +
  (document.doctype.systemId ? ' "' + document.doctype.systemId + '"' : '') +
  '>\n' + document.documentElement.outerHTML;
  document.querySelector('form[action="https://validator.w3.org/check"] > input[name="fragment"]').value = html;
});



/* I took this part from Finance
 Autosubmit the form */
window.onload = function() {
  document.getElementById('autoSubmitForm').submit();
};
