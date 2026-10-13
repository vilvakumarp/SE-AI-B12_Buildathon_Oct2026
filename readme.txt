Use the google drive link to download the data.
https://drive.google.com/drive/folders/16dnfsPPP30cnn5VC4Z0GDY1MCc6vUSqp?usp=sharing


keep this folder after un-zip in the same location of the py scripts.




Note:
1) Run the playwright script - "1 - extract_agrisnet.py" to extract the data as json and validate using "1a - validate_agrisnet.py"
Refer: "1 -Recording extracting schemes from websource using playwright.mp4"

2) Run the "2 build_knowledge_base.py" to initiate - embedding and vectorization - using faiss 
Refer : "2 building knowledge base using FIASS.png"
3) Run main_app.py as streamlit run main_app.py in terminal
Refer : "2 -Recording uzhavar nanban streamlit.mp4"
4) Other files like - "document_loader.py", "guardrails.py", "rag_pipeline.py", "scheme_catalog.py" etc are provided to support the "main_app.py" (these supporting files are imported in appropriate files. for eg - "guardrails.py" have function valid_input).
5) Using langsmith - the OpenAI usage are tracked.
Refer : "API usage - track on Langsmith.png"