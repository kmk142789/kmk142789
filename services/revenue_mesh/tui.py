import curses
from services.revenue_mesh.billing import get_conn


def dashboard(stdscr):
    curses.curs_set(0)

    while True:
        stdscr.clear()

        conn = get_conn()

        total = conn.execute("SELECT COALESCE(SUM(total_price_cents),0) as s FROM jobs").fetchone()['s']
        paid = conn.execute("SELECT COALESCE(SUM(amount_cents),0) as s FROM payments").fetchone()['s']

        stdscr.addstr(1, 2, "Echo Revenue Mesh Dashboard")
        stdscr.addstr(3, 2, f"Total billed: ${total/100:.2f}")
        stdscr.addstr(4, 2, f"Total paid : ${paid/100:.2f}")

        stdscr.addstr(6, 2, "Press q to quit, r to refresh.")

        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break


def main():
    curses.wrapper(dashboard)


if __name__ == "__main__":
    main()
