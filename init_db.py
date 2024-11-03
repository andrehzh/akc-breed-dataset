import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv


class DatabaseInitializer:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Database connection parameters
        self.db_params = {
            'dbname': os.getenv('DB_NAME', 'dog_breeds_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }

        self.conn = None
        self.cur = None

    def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            # Connect to default PostgreSQL database
            conn = psycopg2.connect(
                dbname='postgres',
                user=self.db_params['user'],
                password=self.db_params['password'],
                host=self.db_params['host']
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            # Check if database exists
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                        (self.db_params['dbname'],))
            exists = cur.fetchone()

            if not exists:
                cur.execute(f"CREATE DATABASE {self.db_params['dbname']}")
                print(
                    f"Database {self.db_params['dbname']} created successfully!")
            else:
                print(f"Database {self.db_params['dbname']} already exists.")

            cur.close()
            conn.close()

        except Exception as e:
            print(f"Error creating database: {e}")
            raise e

    def connect(self):
        """Connect to the database"""
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cur = self.conn.cursor()
            print("Connected to database successfully!")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise e

    def create_tables(self):
        """Create the necessary tables"""
        try:
            # Create dog_breeds table
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS dog_breeds (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    breed_group VARCHAR(50),
                    origin VARCHAR(50),
                    temperament TEXT,
                    life_expectancy VARCHAR(20),
                    year_recognized INTEGER,
                    popularity INTEGER,
                    
                    -- Detailed Information
                    grooming TEXT,
                    exercise TEXT,
                    nutrition TEXT,
                    health TEXT,
                    training TEXT,
                    
                    -- Traits (1-5 scale)
                    adaptability INTEGER CHECK (adaptability BETWEEN 1 AND 5),
                    affectionate_with_family INTEGER CHECK (affectionate_with_family BETWEEN 1 AND 5),
                    barking_level INTEGER CHECK (barking_level BETWEEN 1 AND 5),
                    coat_grooming_frequency INTEGER CHECK (coat_grooming_frequency BETWEEN 1 AND 5),
                    drooling_level INTEGER CHECK (drooling_level BETWEEN 1 AND 5),
                    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 5),
                    good_with_other_dogs INTEGER CHECK (good_with_other_dogs BETWEEN 1 AND 5),
                    good_with_young_children INTEGER CHECK (good_with_young_children BETWEEN 1 AND 5),
                    mental_stimulation_needs INTEGER CHECK (mental_stimulation_needs BETWEEN 1 AND 5),
                    openness_to_strangers INTEGER CHECK (openness_to_strangers BETWEEN 1 AND 5),
                    playfulness_level INTEGER CHECK (playfulness_level BETWEEN 1 AND 5),
                    shedding_level INTEGER CHECK (shedding_level BETWEEN 1 AND 5),
                    trainability_level INTEGER CHECK (trainability_level BETWEEN 1 AND 5),
                    watchdog_protective_nature INTEGER CHECK (watchdog_protective_nature BETWEEN 1 AND 5),
                    
                    -- Arrays for multiple values
                    coat_type TEXT[],
                    coat_length TEXT[],
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            self.cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_breed_name ON dog_breeds(name);
                CREATE INDEX IF NOT EXISTS idx_breed_group ON dog_breeds(breed_group);
            """)

            self.conn.commit()
            print("Tables created successfully!")

        except Exception as e:
            self.conn.rollback()
            print(f"Error creating tables: {e}")
            raise e

    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed.")


def main():
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""
DB_NAME=dog_breeds_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
            """.strip())
        print("Created .env file. Please update it with your database credentials.")
        return

    db = DatabaseInitializer()

    try:
        # Create database if it doesn't exist
        db.create_database()

        # Connect to the database
        db.connect()

        # Create tables
        db.create_tables()

    except Exception as e:
        print(f"Failed to initialize database: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
