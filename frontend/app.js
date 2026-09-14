const BACKEND_URL = "http://localhost:8000";

async function loadLoans() {
    const response = await fetch(`${BACKEND_URL}/loans`);
    const loans = await response.json();

    const container = document.getElementById("loans");

    if (loans.length === 0) {
        container.innerHTML = "<p>No loans found.</p>";
        return;
    }

    container.innerHTML = loans
        .map(
            (loan) => `
                <div>
                    <strong>${loan.borrower_name}</strong>
                    - ₹${loan.amount}
                    - ${loan.status}
                </div>
            `
        )
        .join("");
}

document
    .getElementById("loan-form")
    .addEventListener("submit", async (event) => {
        event.preventDefault();

        const loan = {
            borrower_name: document.getElementById("borrower_name").value,
            amount: Number(
                document.getElementById("loan_amount").value
            ),
            status: document.getElementById("status").value
        };

        const response = await fetch(`${BACKEND_URL}/loans`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(loan)
        });

        if (!response.ok) {
            alert("Failed to create loan");
            return;
        }

        event.target.reset();
        await loadLoans();
    });

loadLoans();