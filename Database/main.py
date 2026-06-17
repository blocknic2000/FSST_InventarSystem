import mysql.connector
import config


class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host=config.Database.HOST,
            user=config.Database.USER,
            password=config.Database.PASSWORD,
            database=config.Database.DATABASE
        )

        self.cursor = self.connection.cursor(
            dictionary=True
        )

    # --------------------------------------------------
    # Logs
    # --------------------------------------------------

    def add_log(
        self,
        username: str,
        action: str
    ):
        self.cursor.execute(
            """
            INSERT INTO admin_logs
            (
                username,
                action,
                created_at
            )
            VALUES
            (
                %s,
                %s,
                NOW()
            )
            """,
            (
                username,
                action
            )
        )

        self.connection.commit()

    # --------------------------------------------------
    # Artikel
    # --------------------------------------------------

    def get_articles(self):

        self.cursor.execute(
            """
            SELECT *
            FROM Artikel
            ORDER BY ArtikelName
            """
        )

        return self.cursor.fetchall()

    def get_article_by_id(
        self,
        artikel_id: int
    ):

        self.cursor.execute(
            """
            SELECT *
            FROM Artikel
            WHERE ArtikelID = %s
            """,
            (artikel_id,)
        )

        return self.cursor.fetchone()

    def create_article(
        self,
        artikel_id: int,
        artikel_name: str,
        typ: str,
        menge: int,
        image: str = None,
        status: str = "active"
    ):

        self.cursor.execute(
            """
            INSERT INTO Artikel
            (
                ArtikelID,
                ArtikelName,
                Typ,
                Menge,
                image,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                artikel_id,
                artikel_name,
                typ,
                menge,
                image,
                status
            )
        )

        self.connection.commit()

    def update_article(
        self,
        artikel_id: int,
        artikel_name: str,
        typ: str,
        menge: int,
        image: str,
        status: str
    ):

        self.cursor.execute(
            """
            UPDATE Artikel
            SET
                ArtikelName=%s,
                Typ=%s,
                Menge=%s,
                image=%s,
                status=%s
            WHERE ArtikelID=%s
            """,
            (
                artikel_name,
                typ,
                menge,
                image,
                status,
                artikel_id
            )
        )

        self.connection.commit()

    def delete_article(
        self,
        artikel_id: int
    ):

        self.cursor.execute(
            """
            UPDATE Artikel
            SET status='deleted'
            WHERE ArtikelID=%s
            """,
            (artikel_id,)
        )

        self.connection.commit()

    # --------------------------------------------------
    # Ausgeliehen
    # --------------------------------------------------

    def lend_article(
        self,
        artikel_id: int,
        menge: int,
        name: str,
        klasse: str
    ):

        self.cursor.execute(
            """
            INSERT INTO ausgeliehen
            (
                ArtikelID,
                Menge,
                Name,
                Klasse
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                artikel_id,
                menge,
                name,
                klasse
            )
        )

        self.cursor.execute(
            """
            UPDATE Artikel
            SET Menge = Menge - %s
            WHERE ArtikelID=%s
            """,
            (
                menge,
                artikel_id
            )
        )

        self.connection.commit()

    def return_article(
        self,
        lend_id: int
    ):

        self.cursor.execute(
            """
            SELECT *
            FROM ausgeliehen
            WHERE id=%s
            """,
            (lend_id,)
        )

        data = self.cursor.fetchone()

        if not data:
            return False

        self.cursor.execute(
            """
            UPDATE ausgeliehen
            SET returned=1
            WHERE id=%s
            """,
            (lend_id,)
        )

        self.cursor.execute(
            """
            UPDATE Artikel
            SET Menge = Menge + %s
            WHERE ArtikelID=%s
            """,
            (
                data["Menge"],
                data["ArtikelID"]
            )
        )

        self.connection.commit()

        return True

    def get_lendings(self):

        self.cursor.execute(
            """
            SELECT *
            FROM ausgeliehen
            ORDER BY Zeitpunkt DESC
            """
        )

        return self.cursor.fetchall()

    # --------------------------------------------------
    # Reservierungen
    # --------------------------------------------------

    def create_reservation(
        self,
        artikel_id: int,
        name: str,
        klasse: str,
        menge: int,
        von,
        bis
    ):

        self.cursor.execute(
            """
            INSERT INTO reservierte
            (
                ArtikelID,
                Name,
                Klasse,
                Menge,
                von,
                bis
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                artikel_id,
                name,
                klasse,
                menge,
                von,
                bis
            )
        )

        self.connection.commit()

    def finish_reservation(
        self,
        reservation_id: int
    ):

        self.cursor.execute(
            """
            UPDATE reservierte
            SET finished=1
            WHERE id=%s
            """,
            (reservation_id,)
        )

        self.connection.commit()

    def get_reservations(self):

        self.cursor.execute(
            """
            SELECT *
            FROM reservierte
            ORDER BY Zeitpunkt DESC
            """
        )

        return self.cursor.fetchall()

    # --------------------------------------------------
    # Dashboard
    # --------------------------------------------------

    def get_dashboard_stats(self):

        self.cursor.execute(
            "SELECT COUNT(*) AS count FROM Artikel"
        )
        artikel = self.cursor.fetchone()["count"]

        self.cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM ausgeliehen
            WHERE returned=0
            """
        )
        ausgeliehen = self.cursor.fetchone()["count"]

        self.cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM reservierte
            WHERE finished=0
            """
        )
        reserviert = self.cursor.fetchone()["count"]

        return {
            "artikel": artikel,
            "ausgeliehen": ausgeliehen,
            "reserviert": reserviert
        }

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close(self):

        self.cursor.close()
        self.connection.close()