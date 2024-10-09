import oci
from dotenv import load_dotenv
from langchain.chains import create_sql_query_chain
from langchain_community.chat_models import ChatOCIGenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import constants as c

load_dotenv()


def get_llm_model():
    if not c.IS_OCI_CREDENTIALS_VALID:
        return
    client = oci.generative_ai_inference.GenerativeAiInferenceClient(
        config=c.OCI_CREDENTIALS,
        service_endpoint=c.DEFAULT_GENAI_SERVICE_ENDPOINT,
    )
    model = ChatOCIGenAI(
        model_id='cohere.command-r-plus',
        service_endpoint=c.DEFAULT_GENAI_SERVICE_ENDPOINT,
        compartment_id=c.DEFAULT_COMPARTMENT_ID,
        model_kwargs={
            'max_tokens': c.MAX_TOKENS,
            'temperature': 0.1,
        },
        client=client,
    )
    return model


def sql_agent(llm, db=None, toolkit=None):
    chain = create_sql_query_chain(llm, db)

    prompt = ChatPromptTemplate.from_messages(
        [('system', c.system), ('human', '{query}')]
    ).partial(
        dialect=db.dialect,
        tables_names=db.get_usable_table_names()[0],
    )

    validation_chain = prompt | llm | StrOutputParser()

    full_chain = {'query': chain} | validation_chain
    full_chain.get_prompts()[0].pretty_print()

    return full_chain
