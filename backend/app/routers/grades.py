from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_role
from app.models.grade import Grade
from app.models.student import Student
from app.schemas.grade import GradeCreate, GradeOut, GradeUpdate
from app.services.class_order import class_sort_key

router = APIRouter(prefix="/api/grades", tags=["grades"])


@router.get("", response_model=list[GradeOut])
def list_grades(db: Session = Depends(get_db)):
    grades = db.execute(select(Grade)).scalars().all()
    # Natural class order (Playgroup → Grade 10) so every class dropdown and the
    # Grades page read in the sequence the school actually uses.
    grades = sorted(grades, key=lambda g: class_sort_key(g.class_name))
    counts = dict(
        db.execute(
            select(Student.class_name, func.count(Student.student_id))
            .where(Student.status == "Active")
            .group_by(Student.class_name)
        ).all()
    )
    return [
        GradeOut(grade_id=g.grade_id, class_name=g.class_name, fee_amount=float(g.fee_amount), student_count=counts.get(g.class_name, 0))
        for g in grades
    ]


@router.post("", response_model=GradeOut, dependencies=[Depends(require_role("Admin"))])
def add_grade(payload: GradeCreate, db: Session = Depends(get_db)):
    grade = Grade(class_name=payload.class_name, fee_amount=payload.fee_amount)
    db.add(grade)
    db.commit()
    return grade


@router.put("/{grade_id}", response_model=GradeOut, dependencies=[Depends(require_role("Admin"))])
def update_grade(grade_id: int, payload: GradeUpdate, db: Session = Depends(get_db)):
    grade = db.get(Grade, grade_id)
    if grade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Grade not found")
    grade.class_name = payload.class_name
    grade.fee_amount = payload.fee_amount
    db.commit()
    return grade


@router.delete("/{grade_id}", dependencies=[Depends(require_role("Admin"))])
def delete_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = db.get(Grade, grade_id)
    if grade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Grade not found")
    enrolled = db.execute(
        select(func.count(Student.student_id)).where(Student.class_name == grade.class_name)
    ).scalar_one()
    if enrolled > 0:
        student_word = "student" if enrolled == 1 else "students"
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot delete '{grade.class_name}' — {enrolled} {student_word} currently enrolled in this class. "
            "Move or promote them to another class first.",
        )
    db.delete(grade)
    db.commit()
    return {"detail": "Deleted"}
