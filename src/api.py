


 system_prompt = """
            You will be provided with two entities and related text. Your task is to extract their relationship and provide a JSON response.

            The JSON should include the following fields:
            1. "Entity 1": The first entity provided in the input.
            2. "Entity 2": The second entity provided in the input.
            3. "Relationship Summary": A concise summary of the relationship between Entity 1 and Entity 2, based on the given text.
            4. "Confidence Score": A numerical score (in percentage, 0-100%) indicating your confidence in the relationship summary.
            5. "Relevant Context": A short snippet of text from the input that supports the relationship summary.
            6. "Threat Assessment":
                - "Level": A numerical threat level from 1 (low threat) to 10 (high threat), if it is clear that there is a threat, give a higher score. If it is clear that there is no threat give lower.
                - "Type": A concise label for the type of threat you can come up with your own. You must indicate who is the actor and who is being acted upon (e.g., "Cybersecurity", "Espionage", "Economic", "Diplomatic","Terrorism").
                - "Explanation": A short explanation of the threat level and type based on the context.

            EXAMPLE INPUT:
            Entity 1: Entity_A
            Entity 2: Entity_B
            Text: Entity_A collaborated with Entity_B to conduct sensitive operations that involved data breaches.

            EXAMPLE JSON OUTPUT:
            {
                "Entity 1": "Entity_A",
                "Entity 2": "Entity_B",
                "Relationship Summary": "Entity_A collaborated with Entity_B on sensitive operations involving data breaches.",
                "Confidence Score": "90%",
                "Relevant Context": "Entity_A collaborated with Entity_B to conduct sensitive operations that involved data breaches.",
                "Threat Assessment": {
                    "Level": 8,
                    "Type": "Cybersecurity",
                    "Explanation": "The collaboration involved data breaches, indicating a high cybersecurity threat."
                }
            }
            """