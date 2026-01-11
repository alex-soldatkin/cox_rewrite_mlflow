We are working on redoing the analysis present in a thesis. The paths to the old files are in the .env file. You have only read-only access to the old files. 

We are using mlflow for experiment tracking. The mlflow server is running on http://localhost:5000. Each model should be run in a separate experiment. 

We are using statsmodels and scikit-learn for statistical analysis. 

We are using lifelines for survival analysis. The documentation is available in ./lifelines_docs/docs directory. Examples are available in ./lifelines_docs/examples.

We are using Neo4j for graph analysis. You are allowed read-only access to the Neo4j database based on the .env file using either cypher-shell tool or the Graph Data Science (GDS) library. You are not allowed to modify the Neo4j database. You can see the current Neo4j schema by running `cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD -c "CALL db.schema.visualization()"`. You should make a separate script to read in the .env creds for Neo4j and use them every time you run a cypher-shell command. If you find yourself resuing the same cypher queries, put them into ./queries/cypher directory. If a Cypher query is required in Python, put it into the same directory and import it. Always start query name with a number, 3-digit zero-padded.

We are using Lets-Plot for data visualisation. You should read `memory-bank/LETS_PLOT_BEST_PRACTICES.md` for best practices IF asked to visualise something. 

We are using `uv` for env management and for running scripts. To add a package, use `uv add <package_name>`. To remove a package, use `uv remove <package_name>`. To run a script, use `uv run <script_name>`. To activate the environment, use `source .venv/bin/activate`.

We are using Pydantic to build data models for data processing, data acquisition, and graph analysis. Store them in ./data_models directory.

We are using the ./memory-bank folder in the cwd to store any relevant information that you may need to remember. 

You will keep the Python code very modular with proper subdirectories and make it conform to Pydantic schema. If you find any external directory you keep doing back to, make a new .env variable for it and store it in the .env file.

You will use strictly British English for all your responses: "colour" instead of "color", "organisation" instead of "organization", etc.