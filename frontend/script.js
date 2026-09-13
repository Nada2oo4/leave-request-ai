const form = document.getElementById("leaveForm");
const submitBtn = document.getElementById("submitBtn");
const attachmentInput = document.getElementById("attachment");
const fileName = document.getElementById("fileName");
const resultContainer = document.getElementById("resultContainer");


/* Show selected file */

attachmentInput.addEventListener("change", () => {

    if (attachmentInput.files.length > 0) {
        fileName.textContent = `📎 ${attachmentInput.files[0].name}`;
    } else {
        fileName.textContent = "";
    }

});


/* Submit */

form.addEventListener("submit", async (event) => {

    event.preventDefault();

    submitBtn.disabled = true;
    submitBtn.innerHTML = "⏳ Evaluating...";

    resultContainer.innerHTML = `
        <div class="result-placeholder">
            <div class="placeholder-icon">✦</div>
            <h3>AI is evaluating...</h3>
            <p>
                Checking the request against company policy
                and analyzing supporting documents.
            </p>
        </div>
    `;


    const formData = new FormData();

    formData.append(
        "employee_id",
        document.getElementById("employee_id").value
    );

    formData.append(
        "country",
        document.getElementById("country").value
    );

    formData.append(
        "leave_type",
        document.getElementById("leave_type").value
    );

    formData.append(
        "start_date",
        document.getElementById("start_date").value
    );

    formData.append(
        "end_date",
        document.getElementById("end_date").value
    );

    formData.append(
        "reason",
        document.getElementById("reason").value
    );


    const joiningDate =
        document.getElementById("date_of_joining").value;

    if (joiningDate) {
        formData.append("date_of_joining", joiningDate);
    }


    if (attachmentInput.files.length > 0) {
        formData.append(
            "attachment",
            attachmentInput.files[0]
        );
    }


    try {

        const response = await fetch(
            "http://127.0.0.1:8000/leave-request",
            {
                method: "POST",
                body: formData
            }
        );


        if (!response.ok) {

            const errorData = await response.json();

            throw new Error(
                errorData.detail || "Something went wrong."
            );
        }


        const data = await response.json();

        displayResult(data);


    } catch (error) {

        resultContainer.innerHTML = `
            <div class="result-placeholder">
                <div class="placeholder-icon">!</div>
                <h3>Request Failed</h3>
                <p>${error.message}</p>
            </div>
        `;

    } finally {

        submitBtn.disabled = false;
        submitBtn.innerHTML = "✦ Evaluate Request";

    }

});


function displayResult(data) {

    let decisionClass = "review";
    let decisionIcon = "⚠";

    if (data.decision === "APPROVED") {
        decisionClass = "approved";
        decisionIcon = "✓";
    }

    else if (data.decision === "DENIED") {
        decisionClass = "denied";
        decisionIcon = "✕";
    }

    else if (data.decision === "ATTACHMENT_REQUIRED") {
        decisionClass = "review";
        decisionIcon = "📎";
    }


    let evidenceHTML = "";

    if (
        data.policy_evidence &&
        data.policy_evidence.length > 0
    ) {

        evidenceHTML = data.policy_evidence
            .map(evidence => `
                <div class="policy-evidence">

                    <strong>
                        📄 Page ${evidence.page ?? "N/A"}
                    </strong>

                    <p>
                        ${evidence.text ?? "No evidence text available."}
                    </p>

                </div>
            `)
            .join("");

    } else {

        evidenceHTML = `
            <p>No policy evidence available.</p>
        `;
    }


    resultContainer.innerHTML = `

        <div class="result-content">

            <div class="decision ${decisionClass}">

                <h3>
                    ${decisionIcon}
                    ${formatDecision(data.decision)}
                </h3>

                <p>
                    AI-generated evaluation
                </p>

            </div>


            <div class="info-grid">

                <div class="info-box">

                    <div class="label">
                        REQUESTED DAYS
                    </div>

                    <div class="value">
                        ${data.requested_days ?? "—"} days
                    </div>

                </div>


                <div class="info-box">

                    <div class="label">
                        ATTACHMENT
                    </div>

                    <div class="value">
                        ${
                            data.attachment_required
                                ? (
                                    data.attachment_present
                                        ? "Provided"
                                        : "Required"
                                )
                                : "Not Required"
                        }
                    </div>

                </div>

            </div>


            <div class="result-section">

                <h4>AI Reasoning</h4>

                <p>
                    ${data.reason ?? "No explanation available."}
                </p>

            </div>


            ${
                data.attachment_analysis
                ? `
                    <div class="result-section">

                        <h4>Attachment Analysis</h4>

                        <p>
                            ${data.attachment_analysis}
                        </p>

                    </div>
                `
                : ""
            }


            <div class="result-section">

                <h4>Policy Evidence</h4>

                ${evidenceHTML}

            </div>

        </div>
    `;
}


function formatDecision(decision) {

    if (!decision) {
        return "REVIEW REQUIRED";
    }

    return decision
        .replaceAll("_", " ")
        .toUpperCase();
}