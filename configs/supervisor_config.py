""" constants to use in the supervisor agent"""
# thread ids are crucial for graph state persistence so there should be unique for each agent key.
THREAD_IDS = {
    'RAG':'1',
    'Architect':'2',
    'Planner':'3',
    'Coder':'4'
}

# Currently only use this value for collection_name if you have embeded and saved vector into the db with a differnet name then you can use it here.
VECTOR_DB_COLLECTIONS = {'MISMO-version-3.6-docs':"C:/Users/vkumar/Desktop/genpod-ai-backend/vector_collections"}

MEMBERS = ['RAG','Architect','Planner']

# VECTOR_DB_PERSISTENCE_LOCATION = "C:/Users/vkumar/Desktop/genpod-ai-backend/vector_collections"