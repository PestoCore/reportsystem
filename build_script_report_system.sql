CREATE TABLE report_category(
	id SERIAL PRIMARY KEY,
	category_name VARCHAR(32) NOT NULL
);

CREATE INDEX idx_report_category_category_name ON report_category(category_name);

CREATE TABLE status_category(
	id SERIAL PRIMARY KEY,
	status_name VARCHAR(32) NOT NULL
);

CREATE INDEX idx_status_category_status_name ON status_category(status_name);

CREATE TABLE report(
	id SERIAL PRIMARY KEY,
	report_category_id INT NOT NULL,
	CONSTRAINT fk_report_report_category 
		FOREIGN KEY (report_category_id) 
		REFERENCES report_category(id) 
		ON DELETE SET NULL 
		ON UPDATE CASCADE,
	description VARCHAR(256),
	report_location GEOMETRY(Point, 2180) NOT NULL,
	time_of_submission TIMESTAMP NOT NULL,
	status_category_id INT NOT NULL,
	CONSTRAINT fk_report_status_category 
		FOREIGN KEY (status_category_id) 
		REFERENCES status_category(id) 
		ON DELETE SET NULL
);

UPDATE report
SET report_location = ST_SetSRID(report_location, 2180)
WHERE report_location IS NOT NULL;

CREATE INDEX idx_report_report_category_id ON report(report_category_id);
CREATE INDEX idx_report_status_category_id ON report(status_category_id);

INSERT INTO report_category (category_name) 
VALUES
	('Drogi'),
	('Parkowanie'),
	('Komunikacja'),
	('Lokalowe'),
	('Odśnieżanie'),
	('Śmieci'),
	('Uszkodzenie, dewastacja'),
	('Wodno-kanalizacyjne'),
	('Zieleń'),
	('Zwierzęta'),
	('Inne'),
	('Porządek i bezpieczeństwo');

INSERT INTO status_category (status_name) 
VALUES
	('Przyjęte'),
	('W trakcie realizacji'),
	('Zrealizowane'),
	('Odrzucone');

INSERT INTO report (
    report_category_id, 
    description, 
    report_location, 
    time_of_submission, 
    status_category_id
) 
VALUES (
    11,
    'Pierwsze zgłoszenie testowe',
    ST_SetSRID(ST_Point(21.0122, 52.2298), 2180),
    NOW(),
    3
);
