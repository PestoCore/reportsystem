from typing import Union

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from shapely import wkb, wkt
from fastapi.encoders import jsonable_encoder
from models import Report, ReportCreate, StatusUpdate
from db_config import ORMBaseModel, db_engine, get_db_session
from encoders import to_dict
from datetime import datetime

# niestety
import time
time.sleep(15)

ORMBaseModel.metadata.create_all(bind=db_engine)
app = FastAPI()

# POST

@app.post("/report", status_code=201)
def create_report(report_create: ReportCreate, db_session: Session = Depends(get_db_session)):
    try:
        position_geom = wkt.loads(report_create.report_location)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid position WKT format")
    if not( 1 <= report_create.report_category_id <= 12 ):
        raise HTTPException(status_code=400, detail="Value of report_category_id out of range(1-12)")
    if not( 1 <= report_create.status_category_id <= 4 ):
        raise HTTPException(status_code=400, detail="Value of status_category_id out of range(1-4)")
    new_report = Report(
        report_category_id=report_create.report_category_id,
        description=report_create.description,
        time_of_submission=report_create.time_of_submission,
        status_category_id=report_create.status_category_id,
        report_location=f"SRID=2180;{report_create.report_location}"
    )
    db_session.add(new_report)
    db_session.commit()
    db_session.refresh(new_report)
    return jsonable_encoder({
        "id": new_report.id,
        "report_category_id": new_report.report_category_id,
        "description": new_report.description,
        "report_location": {
            "x": position_geom.x,
            "y": position_geom.y
        },
        "time_of_submission": new_report.time_of_submission,
        "status_category_id": new_report.status_category_id
    })

# GET

@app.get("/")
def test():
    return {"msg": "Jeśli to widać, działa :3"}

@app.get("/report")
def get_all_reports(db_session: Session = Depends(get_db_session)):
    reports = db_session.query(Report).all()
    result = []
    for report in reports:
        report_dict = to_dict(report)
        if report.report_location:
            position_geom = wkb.loads(bytes(report.report_location.data))
            report_dict['report_location'] = {
                "x": position_geom.x,
                "y": position_geom.y
            }
        result.append(report_dict)
    return jsonable_encoder(result)

@app.get("/report/{report_id}")
def get_report(report_id: int, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.report_location:
        raise HTTPException(status_code=404, detail="Position not available")
    position_geom = wkb.loads(bytes(report.report_location.data))
    return jsonable_encoder({
        "id": report.id,
        "report_category_id": report.report_category_id,
        "description": report.description,
        "report_location": {
            "x": position_geom.x,
            "y": position_geom.y
        },
        "time_of_submission": report.time_of_submission,
        "status_category_id": report.status_category_id
    })

@app.get("/report/{report_id}/report_location")
def get_report_location(report_id: int, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.report_location:
        raise HTTPException(status_code=404, detail="Position not available")
    position_geom = wkb.loads(bytes(report.report_location.data))
    return jsonable_encoder({
        "position": {
            "x": position_geom.x,
            "y": position_geom.y
        }
    })

@app.get("/report/{report_id}/status_category_id")
def get_report_location(report_id: int, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.report_location:
        raise HTTPException(status_code=404, detail="Position not available")
    position_geom = wkb.loads(bytes(report.report_location.data))
    return jsonable_encoder({
        "status_category_id": report.status_category_id
    })

# PUT

@app.put("/report/{report_id}/status_category_id")
def update_status(report_id: int, status_update: StatusUpdate, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not( 1 <= status_update.status_category_id <= 4 ):
        raise HTTPException(status_code=400, detail="Value of status_category_id out of range(1-4)")
    report.status_category_id = status_update.status_category_id
    db_session.commit()
    db_session.refresh(report)
    return jsonable_encoder({
        "message": "Status updated",
        "id": report.id,
        "status_category_id": status_update.status_category_id
    })

# DELETE

@app.delete("/report/{report_id}")
def delete_report(report_id: int, db_session: Session = Depends(get_db_session)):
    report = db_session.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db_session.delete(report)
    db_session.commit()
    return jsonable_encoder({"message": "Report deleted"})
