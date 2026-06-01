from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Question, QuizAttempt, QuizAnswer
import random


def get_option(q, key):
    option_map = {
        "A": {"key": "A", "text": q.option_a_text, "image": q.option_a_image},
        "B": {"key": "B", "text": q.option_b_text, "image": q.option_b_image},
        "C": {"key": "C", "text": q.option_c_text, "image": q.option_c_image},
        "D": {"key": "D", "text": q.option_d_text, "image": q.option_d_image},
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
        user_option = None
        is_correct = None

        if submitted and request is not None:
            user_answer = request.POST.get(str(q.id), "")
            is_correct = user_answer == q.answer

            for option in options:
                if option["value"] == user_answer:
                    user_display_answer = option["display_key"]
                    user_option = option

        correct_option = None
        for option in options:
            if option["key"] == q.answer:
                correct_option = option

        question_data.append({
            "question": q,
            "options": options,
            "option_order": order,
            "user_answer": user_answer,
            "user_display_answer": user_display_answer,
            "user_option": user_option,
            "correct_answer": q.answer,
            "correct_option": correct_option,
            "is_correct": is_correct,
        })

    return question_data


@login_required
def home(request):
    score = None
    submitted = False
    question_data = []
    duration_seconds = None
    attempt = None
    time_limit_seconds = 300
    selected_count = 10

    if request.method == "GET":
        if request.GET.get("start") != "1":
            return render(request, "home.html", {
                "question_data": [],
                "score": score,
                "submitted": submitted,
                "duration_seconds": duration_seconds,
                "attempt": attempt,
                "time_limit_seconds": time_limit_seconds,
                "waiting_to_start": True,
            })
        try:
            count = int(request.GET.get("count", 10))
        except ValueError:
            count = 10

        if count not in [5, 10]:
            count = 10

        selected_count = count
        
        if count == 5:
            time_limit_seconds = 300
        else:
            time_limit_seconds = 600

        all_questions = list(Question.objects.all())

        wrong_question_ids = request.session.get("wrong_question_ids", [])
        wrong_questions = list(Question.objects.filter(id__in=wrong_question_ids))

        wrong_question_map = {q.id: q for q in wrong_questions}
        ordered_wrong_questions = [
            wrong_question_map[qid]
            for qid in wrong_question_ids
            if qid in wrong_question_map
        ]

        other_questions = [q for q in all_questions if q.id not in wrong_question_ids]

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
        request.session["quiz_started_at"] = timezone.now().isoformat()
        request.session["time_limit_seconds"] = time_limit_seconds

        question_data = build_question_data(questions, option_orders)

    else:
        submitted = True

        question_ids = request.session.get("question_ids", [])
        option_orders = request.session.get("option_orders", {})
        started_at_text = request.session.get("quiz_started_at")
        time_limit_seconds = request.session.get("time_limit_seconds", 300)

        if started_at_text:
            started_at = timezone.datetime.fromisoformat(started_at_text)
        else:
            started_at = timezone.now()

        finished_at = timezone.now()
        duration_seconds = max(0, int((finished_at - started_at).total_seconds()))

        questions_map = {
            q.id: q
            for q in Question.objects.filter(id__in=question_ids)
        }

        questions = [
            questions_map[qid]
            for qid in question_ids
            if qid in questions_map
        ]

        question_data = build_question_data(
            questions,
            option_orders,
            request=request,
            submitted=True,
        )

        wrong_question_ids = request.session.get("wrong_question_ids", [])
        correct_count = 0

        for item in question_data:
            q = item["question"]

            if item["is_correct"]:
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

        next_attempt_number = (
            QuizAttempt.objects.filter(user=request.user).count() + 1
        )

        attempt = QuizAttempt.objects.create(
            user=request.user,
            user_attempt_number=next_attempt_number,
            question_count=len(questions),
            score=score,
            correct_count=correct_count,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
        )

        for index, item in enumerate(question_data, start=1):
            QuizAnswer.objects.create(
                attempt=attempt,
                question=item["question"],
                display_number=index,
                option_order=",".join(item["option_order"]),
                user_answer=item["user_answer"] or "",
                user_display_answer=item["user_display_answer"] or "",
                user_answer_text=item["user_option"]["text"] if item["user_option"] else "",
                correct_answer=item["correct_answer"],
                correct_display_answer=item["correct_option"]["display_key"],
                correct_answer_text=item["correct_option"]["text"] if item["correct_option"] else "",
                is_correct=item["is_correct"],
            )

    return render(request, "home.html", {
        "question_data": question_data,
        "score": score,
        "submitted": submitted,
        "duration_seconds": duration_seconds,
        "attempt": attempt,
        "time_limit_seconds": time_limit_seconds,
        "waiting_to_start": False,
        "selected_count": selected_count,
    })


@login_required
def history(request):
    attempts = (
        QuizAttempt.objects
        .filter(user=request.user)
        .prefetch_related("answers", "answers__question")
        .order_by("-started_at")
    )

    return render(request, "history.html", {
        "attempts": attempts,
    })


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {
        "form": form,
    })


def login_user(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )

            if user is not None:
                login(request, user)
                return redirect("home")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {
        "form": form,
    })


def logout_user(request):
    logout(request)
    return redirect("login")