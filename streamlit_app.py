import streamlit as st
from neo4j import GraphDatabase

# Neo4j connection setup
class Neo4jDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        if self.driver:
            self.driver.close()

    # Updated get_disease_info method for exact symptom match (all symptoms required)
    def get_disease_info(self, symptoms):
        # Split the input symptoms by commas and trim any whitespace
        symptom_list = [s.strip() for s in symptoms.split(',') if s.strip()]

        # Query to match diseases indicated by all input symptoms
        query = """
        MATCH (d:Disease)<-[:INDICATES]-(s:Symptom)
        WHERE s.name IN $symptomList
        WITH d, COLLECT(s.name) AS matchedSymptoms
        WHERE apoc.coll.sort(matchedSymptoms) = apoc.coll.sort($symptomList)
        OPTIONAL MATCH (d)-[:TREATED_BY]->(m:Medicine)
        RETURN d.name AS disease, COLLECT(DISTINCT m.name) AS medicines
        """

        with self.driver.session() as session:
            result = session.run(query, symptomList=symptom_list)
            return [{"disease": record["disease"], "medicines": record["medicines"]} for record in result]

# Streamlit app layout
st.title("Disease Ontology: Symptom to Disease Finder")

# Taking Neo4j credentials from Streamlit secrets
uri = st.secrets["neo4j"]["uri"]
username = st.secrets["neo4j"]["username"]
password = st.secrets["neo4j"]["password"]

# Initialize Neo4j connection
db = Neo4jDatabase(uri, username, password)

# User input for symptoms (comma-separated)
symptom_input = st.text_input("Enter symptoms (comma-separated):")

if st.button("Search"):
    if symptom_input:
        # Query the Neo4j database
        results = db.get_disease_info(symptom_input)

        if results:
            st.write(f"Diseases related to the symptoms '{symptom_input}':")
            for item in results:
                st.write(f"Disease: {item['disease']}")
                st.write(f"Medicines: {', '.join(item['medicines']) if item['medicines'] else 'No medicines available'}")
        else:
            st.write("No disease found for the given symptoms.")
    else:
        st.write("Please enter symptoms.")

# Close the Neo4j connection
db.close()
