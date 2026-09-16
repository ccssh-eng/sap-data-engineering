import csv
import os
import struct

import pyodbc


SERVER = "sql-sap-data-7cc1d2.database.windows.net"
DATABASE = "sap-analytics-db"
SERVING_DIR = os.path.expanduser(
    "~/sap-data-engineering/azure/serving"
)

SQL_COPT_SS_ACCESS_TOKEN = 1256


def get_connection(access_token):
    """Create an Azure SQL connection using an Entra access token."""

    token_bytes = access_token.encode("utf-16-le")

    token_struct = struct.pack(
        f"<I{len(token_bytes)}s",
        len(token_bytes),
        token_bytes
    )

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )

    return pyodbc.connect(
        connection_string,
        attrs_before={
            SQL_COPT_SS_ACCESS_TOKEN: token_struct
        }
    )


def read_csv(filename):
    """Read a Serving CSV file."""

    filepath = os.path.join(SERVING_DIR, filename)

    with open(
        filepath,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def load_customer_kpi(conn):
    rows = read_csv("customer_kpi.csv")
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM dbo.customer_kpi")

        sql = """
            INSERT INTO dbo.customer_kpi
            (
                SoldToParty,
                TransactionCurrency,
                TotalRevenue,
                OrderCount,
                AverageOrderValue
            )
            VALUES (?, ?, ?, ?, ?)
        """

        for row in rows:
            cursor.execute(
                sql,
                row["SoldToParty"],
                row["TransactionCurrency"],
                row["TotalRevenue"],
                int(row["OrderCount"]),
                row["AverageOrderValue"]
            )

        cursor.execute(
            "SELECT COUNT(*) FROM dbo.customer_kpi"
        )

        count = cursor.fetchone()[0]

        if count != len(rows):
            raise RuntimeError(
                "customer_kpi row-count validation failed"
            )

        conn.commit()
        return count

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()


def load_currency_kpi(conn):
    rows = read_csv("currency_kpi.csv")
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM dbo.currency_kpi")

        sql = """
            INSERT INTO dbo.currency_kpi
            (
                TransactionCurrency,
                TotalRevenue,
                OrderCount,
                AverageOrderValue
            )
            VALUES (?, ?, ?, ?)
        """

        for row in rows:
            cursor.execute(
                sql,
                row["TransactionCurrency"],
                row["TotalRevenue"],
                int(row["OrderCount"]),
                row["AverageOrderValue"]
            )

        cursor.execute(
            "SELECT COUNT(*) FROM dbo.currency_kpi"
        )

        count = cursor.fetchone()[0]

        if count != len(rows):
            raise RuntimeError(
                "currency_kpi row-count validation failed"
            )

        conn.commit()
        return count

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()

def load_daily_kpi(conn):
    rows = read_csv("daily_kpi.csv")
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM dbo.daily_kpi")

        sql = """
            INSERT INTO dbo.daily_kpi
            (
                CreationDate,
                TransactionCurrency,
                DailyRevenue,
                OrderCount
            )
            VALUES (?, ?, ?, ?)
        """

        for row in rows:
            cursor.execute(
                sql,
                row["CreationDate"],
                row["TransactionCurrency"],
                row["DailyRevenue"],
                int(row["OrderCount"])
            )

        cursor.execute(
            "SELECT COUNT(*) FROM dbo.daily_kpi"
        )

        count = cursor.fetchone()[0]

        if count != len(rows):
            raise RuntimeError(
                "daily_kpi row-count validation failed"
            )

        conn.commit()
        return count

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()

def main():
    access_token = os.environ.get("AZURE_SQL_ACCESS_TOKEN")

    if not access_token:
        raise RuntimeError(
            "AZURE_SQL_ACCESS_TOKEN is not defined"
        )

    conn = get_connection(access_token)

    try:
        customer_count = load_customer_kpi(conn)
        print(
            f"customer_kpi : {customer_count} rows : PASS"
        )

        currency_count = load_currency_kpi(conn)
        print(
            f"currency_kpi : {currency_count} rows : PASS"
        )

        daily_count = load_daily_kpi(conn)
        print(
            f"daily_kpi    : {daily_count} rows : PASS"
        )

        print("Gold Serving load : PASS")

    finally:
        conn.close()


if __name__ == "__main__":
    main()

