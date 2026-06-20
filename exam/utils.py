import openpyxl

from .models import Question

REQUIRED_HEADERS = [
    'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option'
]


def parse_questions_excel(file, exam):
    """
    Reads an uploaded .xlsx file and creates Question rows for the given exam.
    Returns (created_count, list_of_error_messages).
    """
    try:
        wb = openpyxl.load_workbook(file, data_only=True)
    except Exception as exc:
        return 0, [f'Could not read the Excel file: {exc}']

    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return 0, ['The Excel file is empty.']

    headers = [str(h).strip().lower() if h is not None else '' for h in rows[0]]
    missing = [h for h in REQUIRED_HEADERS if h not in headers]
    if missing:
        return 0, [
            f"Missing required column(s): {', '.join(missing)}. "
            f"Expected headers: {', '.join(REQUIRED_HEADERS)} (and optionally 'marks')."
        ]

    col_index = {h: i for i, h in enumerate(headers)}
    has_marks = 'marks' in col_index

    errors = []
    created = 0
    start_order = exam.questions.count()

    for row_num, row in enumerate(rows[1:], start=2):
        if row is None or all(cell in (None, '') for cell in row):
            continue
        try:
            text = row[col_index['question_text']] if col_index['question_text'] < len(row) else None
            a = row[col_index['option_a']] if col_index['option_a'] < len(row) else None
            b = row[col_index['option_b']] if col_index['option_b'] < len(row) else None
            c = row[col_index['option_c']] if col_index['option_c'] < len(row) else None
            d = row[col_index['option_d']] if col_index['option_d'] < len(row) else None
            correct = row[col_index['correct_option']] if col_index['correct_option'] < len(row) else None

            if not all([text, a, b, c, d, correct]):
                errors.append(f'Row {row_num}: missing a required value, row skipped.')
                continue

            correct = str(correct).strip().upper()
            if correct not in ('A', 'B', 'C', 'D'):
                errors.append(
                    f"Row {row_num}: correct_option must be A, B, C or D (got '{correct}'), row skipped."
                )
                continue

            marks = 1
            if has_marks and col_index['marks'] < len(row) and row[col_index['marks']]:
                try:
                    marks = int(row[col_index['marks']])
                except (ValueError, TypeError):
                    marks = 1

            Question.objects.create(
                exam=exam,
                text=str(text).strip(),
                option_a=str(a).strip(),
                option_b=str(b).strip(),
                option_c=str(c).strip(),
                option_d=str(d).strip(),
                correct_option=correct,
                marks=marks,
                order=start_order + created + 1,
            )
            created += 1
        except Exception as exc:
            errors.append(f'Row {row_num}: error parsing row ({exc}), row skipped.')

    return created, errors
