console.log("instrument_form.js geladen");
document.addEventListener('DOMContentLoaded', function() {
    const select = document.getElementById('id_instrument');
    const dateLabel = document.querySelector('label[for="id_date"]');
    const subjectLabel = document.querySelector('label[for="id_subject"]');
    const considerationsLabel = document.querySelector('label[for="id_considerations"]');
    const instrumentLabel = document.querySelector('label[for="id_instrument"]');
    const requestsLabel = document.querySelector('label[for="id_requests"]');
    const requestsContainer = document.getElementById('id_requests').parentNode;
  
    function updateLabels() {
        const val = select.value;

        // Always reset instrument label
        instrumentLabel.textContent = 'Instrument';

        if (val === 'Mondelinge vragen') {
            dateLabel.textContent = 'Datum vergadering';
            subjectLabel.textContent = 'Onderwerp';
            considerationsLabel.textContent = 'Toelichting';
            requestsLabel.textContent = 'Vragen';
            requestsContainer.style.display = '';
        } else if (val === 'Schriftelijke vragen') {
            dateLabel.textContent = 'Datum indiening';
            subjectLabel.textContent = 'Onderwerp';
            considerationsLabel.textContent = 'Toelichting';
            requestsLabel.textContent = 'Vragen';
            requestsContainer.style.display = '';
        } else if (val === 'Agendapunt' || val === 'Actualiteit') {
            dateLabel.textContent = 'Datum';
            subjectLabel.textContent = 'Onderwerp';
            considerationsLabel.textContent = 'Toelichting';
            requestsLabel.textContent = '';
            requestsContainer.style.display = 'none';
        } else if (val === 'Motie') {
            dateLabel.textContent = 'Datum vergadering';
            subjectLabel.textContent = 'Onderwerp';
            considerationsLabel.textContent = 'Overwegingen';
            requestsLabel.textContent = 'Verzoeken';
            requestsContainer.style.display = '';
        } else {
            dateLabel.textContent = 'Datum';
            subjectLabel.textContent = 'Onderwerp';
            considerationsLabel.textContent = 'Toelichting/overwegingen';
            requestsLabel.textContent = 'Vragen/verzoeken';
            requestsContainer.style.display = '';
        }
    }
  
    select.addEventListener('change', updateLabels);
    updateLabels();  // init bij laden
  });