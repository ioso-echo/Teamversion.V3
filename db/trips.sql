ALTER TABLE trips ADD COLUMN departure_city TEXT;
ALTER TABLE trips ADD COLUMN departure_date TEXT;
ALTER TABLE trips ADD COLUMN arrival_city TEXT;
ALTER TABLE trips ADD COLUMN arrival_date TEXT;
ALTER TABLE trips ADD COLUMN sbb_booking_token TEXT;
ALTER TABLE trips ADD COLUMN sbb_api_token TEXT;

CREATE TABLE IF NOT EXISTS trips (
    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    trip_name TEXT,
    departure_city TEXT,
    departure_date TEXT,
    arrival_city TEXT,
    arrival_date TEXT,
    sbb_booking_token TEXT,
    sbb_api_token TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
