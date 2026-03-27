from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

from models.schemas import ProcessCompanyRequest
from services.pipeline import process_company, process_multiple

app = FastAPI(title="Multi-Agent Lead Intelligence System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Lead Intelligence System is running!"}


@app.post("/process-company")
async def api_process_company(request: ProcessCompanyRequest):
    try:
        print(f"\n📥 Received request: company='{request.company}', location='{request.location}'")
        result = await process_company(request.company, request.location)
        return result
    except Exception as e:
        print(f"❌ API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-excel")
async def api_process_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")

    try:
        print(f"\n📥 Received Excel file: {file.filename}")

        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        print(f"   Columns found: {list(df.columns)}")
        print(f"   Rows: {len(df)}")

        companies_list = []
        for _, row in df.iterrows():
            name = ""
            location = ""

            for col in ["company", "Company", "COMPANY", "name", "Name"]:
                if col in row and pd.notna(row[col]):
                    name = str(row[col]).strip()
                    break

            for col in ["location", "Location", "LOCATION", "city", "City"]:
                if col in row and pd.notna(row[col]):
                    location = str(row[col]).strip()
                    break

            if name:
                companies_list.append({"name": name, "location": location})

        if not companies_list:
            raise HTTPException(
                status_code=400,
                detail="No valid companies found. Excel needs a 'company' (or 'name') column."
            )

        print(f"   Found {len(companies_list)} companies to process")

        results = await process_multiple(companies_list)
        return {"results": results}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Excel processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
