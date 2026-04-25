from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from app.company.models import CompanyProfile
from app.company.storage import delete_profile, load_profile, save_profile

router = APIRouter(prefix="/company", tags=["company"])


@router.post("", response_model=CompanyProfile, status_code=201)
def create_or_update_company(profile: CompanyProfile) -> CompanyProfile:
    save_profile(profile)
    return profile


@router.get("", response_model=CompanyProfile)
def get_company() -> CompanyProfile:
    profile = load_profile()
    if profile is None:
        raise HTTPException(status_code=404, detail="No company profile saved yet.")
    return profile


@router.delete("")
def remove_company() -> Response:
    deleted = delete_profile()
    if not deleted:
        raise HTTPException(status_code=404, detail="No company profile to delete.")
    return Response(status_code=204)
