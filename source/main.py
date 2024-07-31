from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


# Cargamos la bdd
sqlite_uri = "sqlite:///./databases/Chinook_sample.db"
db = SQLDatabase.from_uri(sqlite_uri)

# Cargamos el LLM
llm = ChatOllama(model="llama3:latest", temperature=0)


def get_schema(_):
    return db.get_table_info()


def get_sql_chain():

    # Plantilla del prompt
    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, write a SQL query that would answer the user's question:
    {schema}

    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.
    
    
    For example:
    Question: which 3 artists have the most tracks?
    SQL Query: SELECT ArtistId, COUNT(*) as track_count FROM Track GROUP BY ArtistId ORDER BY track_count DESC LIMIT 3;
    Question: Name 10 artists
    SQL Query: SELECT Name FROM Artist LIMIT 10;
    
    Your turn:
    
    Question: {question}
    SQL Query:
    """

    # Generamos el prompt
    prompt = ChatPromptTemplate.from_template(template)

    return (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm.bind(stop=["\nSQLResult:"])
        | StrOutputParser()
    )


def get_response(user_question):
    sql_chain = get_sql_chain()

    # Plantilla del prompt
    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, question, sql query, and sql response, write a natural language response.
    {schema}

    User question: {question}
    SQL Query: {query}
    SQL Response: {response}
    """

    # Generamos el prompt
    prompt = ChatPromptTemplate.from_template(template)

    full_chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
            schema=get_schema, response=lambda vars: db.run(vars["query"])
        )
        | prompt
        | llm
        | StrOutputParser
    )

    return full_chain.invoke({"question": user_question})


user_question = "how many artists are there in the database?"
# get_sql_chain().invoke({"question": user_question})

response = get_response(user_question)
print(response)
