        <h2 class="h5">Instrument: {{ object.instrument }}</h2>
        <p><strong>Onderwerp:</strong> {{ object.subject }}</p>
        <p><strong>Datum:</strong> {{ object.date }}</p>
        <p><strong>Overwegingen:</strong><br>{{ object.considerations|linebreaks }}</p>
        <p><strong>Verzoeken:</strong><br>{{ object.requests|linebreaks }}</p>
        
        <h3 class="h6 mt-4">Indieners</h3>
        {% if object.submitters.all %}
        <div class="table-responsive">
            <table class="table table-sm table-bordered">
                <thead class="table-light">
                    <tr>
                        <th>Voorletters</th>
                        <th>Achternaam</th>
                        <th>Fractie</th>
                    </tr>
                </thead>
                <tbody>
                    {% for submitter in object.submitters.all %}
                    <tr>
                        <td>{{ submitter.initials }}</td>
                        <td>{{ submitter.lastname }}</td>
                        <td>{{ submitter.party }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
            <p class="text-muted">Geen indieners toegevoegd.</p>
        {% endif %}

        <!-- Export & E-mail export dropdowns -->
        <div class="mt-4 d-flex gap-2">
            <div class="btn-group">
                <button type="button" class="btn btn-secondary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                    Exporteren
                </button>
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item" href="{% url 'submission_preview_pdf' object.pk %}">PDF downloaden</a></li>
                    <li><a class="dropdown-item" href="{% url 'instrument_submission_export_docx' object.pk %}">Word (.docx)</a></li>
                    <li><a class="dropdown-item" href="{% url 'instrument_submission_export_latex' object.pk %}">LaTeX PDF</a></li>
                    <li><a class="dropdown-item" href="{% url 'instrument_submission_export_latex_source' object.pk %}">LaTeX-bron (.tex)</a></li>
                    <li><a class="dropdown-item" href="{% url 'instrument_submission_export_zip' object.pk %}">ZIP downloaden</a></li>
                </ul>
            </div>
            <div class="btn-group">
                <button type="button" class="btn btn-secondary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                    E-mail Export
                </button>
                <ul class="dropdown-menu">
                    <li>
                        <form method="post" action="{% url 'instrument_email_export' object.pk %}">
                            {% csrf_token %}
                            <input type="hidden" name="format" value="pdf">
                            <button type="submit" class="dropdown-item">PDF via e-mail</button>
                        </form>
                    </li>
                    <li>
                        <form method="post" action="{% url 'instrument_email_export' object.pk %}">
                            {% csrf_token %}
                            <input type="hidden" name="format" value="txt">
                            <button type="submit" class="dropdown-item">TXT via e-mail</button>
                        </form>
                    </li>
                    <li>
                        <form method="post" action="{% url 'instrument_email_export' object.pk %}">
                            {% csrf_token %}
                            <input type="hidden" name="format" value="docx">
                            <button type="submit" class="dropdown-item">Word (.docx) via e-mail</button>
                        </form>
                    </li>
                    <li>
                        <form method="post" action="{% url 'instrument_email_export' object.pk %}">
                            {% csrf_token %}
                            <input type="hidden" name="format" value="latex">
                            <button type="submit" class="dropdown-item">LaTeX (.pdf) via e-mail</button>
                        </form>
                    </li>
                    <li>
                        <form method="post" action="{% url 'instrument_email_export' object.pk %}">
                            {% csrf_token %}
                            <input type="hidden" name="format" value="latex_source">
                            <button type="submit" class="dropdown-item">LaTeX-bron (.tex) via e-mail</button>
                        </form>
                    </li>
                </ul>
            </div>
        </div>