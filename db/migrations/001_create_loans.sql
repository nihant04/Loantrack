CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    borrower_name VARCHAR(100) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO loans (borrower_name, amount, status) VALUES
    ('Amit Sharma', 50000.00, 'Pending'),
    ('Priya Patel', 75000.00, 'Approved'),
    ('Rahul Verma', 30000.00, 'Rejected'),
    ('Sneha Joshi', 100000.00, 'Approved'),
    ('Vikram Singh', 45000.00, 'Pending');