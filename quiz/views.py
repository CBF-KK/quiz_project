from django.shortcuts import render
from .models import Question
import random


def get_option(q, key):
    option_map = {
        "A": {
            "key": "A",
            "text": q.option_a_text,
            "image": q.option_a_image,
        },
        "B": {
            "key": "B",
            "text": q.option_b_text,
            "image": q.option_b_image,
        },
        "C": {
            "key": "C",
            "text": q.option_c_text,
            "image": q.option_c_image,
        },
        "D": {
            "key": "D",
            "text": q.option_d_text,
            "image": q.option_d_image,
        },
    }
    return option_map[key].copy()


def build_question_data(questions, option_orders, request=None, submitted=False):
    question_data = []
    display_keys = ["A", "B", "C", "D"]

    for q in questions:
        order = option_orders.get(str(q.id), ["A", "B", "C", "D"])
        options = [get_option(q, key) for key in order]

        for index, option in enumerate(options):
            option["display_key"] = display_keys[index]
            option["value"] = option["key"]

        user_answer = None
        user_display_answer = None
        is_correct = None

        if submitted and request is not None:
            user_answer = request.POST.get(str(q.id))
            is_correct = user_answer == q.answer

            for option in options:
                if option["value"] == user_answer:
                    user_display_answer = option["display_key"]

        correct_option = None
        for option in options:
            if option["key"] == q.answer:
                correct_option = option

        question_data.append({
            "question": q,
            "options": options,
            "user_answer": user_answer,
            "user_display_answer": user_display_answer,
            "correct_answer": q.answer,
            "correct_option": correct_option,
            "is_correct": is_correct,
        })

    return question_data


def home(request):
    score = None
    submitted = False
    question_data = []

    if request.method == "GET":
        try:
            count = int(request.GET.get("count", 10))
        except ValueError:
            count = 10

        if count not in [5, 10]:
            count = 10

        all_questions = list(Question.objects.all())

        wrong_question_ids = request.session.get("wrong_question_ids", [])
        wrong_questions = list(Question.objects.filter(id__in=wrong_question_ids))

        wrong_question_map = {q.id: q for q in wrong_questions}
        ordered_wrong_questions = [
            wrong_question_map[qid]
            for qid in wrong_question_ids
            if qid in wrong_question_map
        ]

        other_questions = [
            q for q in all_questions
            if q.id not in wrong_question_ids
        ]

        random.shuffle(ordered_wrong_questions)
        random.shuffle(other_questions)

        questions = (ordered_wrong_questions + other_questions)[:count]

        option_orders = {}
        for q in questions:
            option_keys = ["A", "B", "C", "D"]
            random.shuffle(option_keys)
            option_orders[str(q.id)] = option_keys

        request.session["question_ids"] = [q.id for q in questions]
        request.session["option_orders"] = option_orders

        question_data = build_question_data(questions, option_orders)

    else:
        submitted = True
        score = 0

        question_ids = request.session.get("question_ids", [])
        option_orders = request.session.get("option_orders", {})

        questions_map = {
            q.id: q
            for q in Question.objects.filter(id__in=question_ids)
        }

        questions = [
            questions_map[qid]
            for qid in question_ids
            if qid in questions_map
        ]

        wrong_question_ids = request.session.get("wrong_question_ids", [])

        correct_count = 0

        for q in questions:
            user_answer = request.POST.get(str(q.id))

            if user_answer == q.answer:
                correct_count += 1

                if q.id in wrong_question_ids:
                    wrong_question_ids.remove(q.id)
            else:
                if q.id not in wrong_question_ids:
                    wrong_question_ids.append(q.id)

        request.session["wrong_question_ids"] = wrong_question_ids

        if questions:
            score = round(correct_count / len(questions) * 100)
        else:
            score = 0

        question_data = build_question_data(
            questions,
            option_orders,
            request=request,
            submitted=True,
        )

    return render(request, "home.html", {
        "question_data": question_data,
        "score": score,
        "submitted": submitted,
    })