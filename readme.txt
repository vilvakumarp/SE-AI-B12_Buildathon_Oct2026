Use the google drive link to download the data.
https://drive.google.com/drive/folders/16dnfsPPP30cnn5VC4Z0GDY1MCc6vUSqp?usp=sharing



-------------------------------------------------------

Note:
1) Run the playwright script - "1 - extract_agrisnet.py" to extract the data as json and validate using "1a - validate_agrisnet.py"
Refer: "1 -Recording extracting schemes from websource using playwright.mp4"

2) Run the "2 build_knowledge_base.py" to initiate - embedding and vectorization - using faiss 
Refer : "2 building knowledge base using FIASS.png"

3) keep this folder after un-zip in the same location of the py scripts.

To test FASTAPI
1) Run Postman and type "http://127.0.0.1:8000/"
test these ends:
GET /health → should return:
Reply : {"status": "ok"}


2) For /ask, use - http://127.0.0.1:8000/health:

on body
{
  "question": "What schemes are available for pumpsets?",
  "language": "English",
  "history": []
}
Try get some results


4) Run main_app.py as streamlit run main_app.py in terminal
Refer : "2 -Recording uzhavar nanban streamlit.mp4"
5) Other files like - "document_loader.py", "guardrails.py", "rag_pipeline.py", "scheme_catalog.py" etc are provided to support the "main_app.py" (these supporting files are imported in appropriate files. for eg - "guardrails.py" have function valid_input).
6) Using langsmith - the OpenAI usage are tracked.
Refer : "API usage - track on Langsmith.png"