from string import Template

intro_prompt = Template('''Provide an expert analysis on what does the company $ticker do, how do they make money, and what are their main expertise. Explain in Korean.''')

cost_prompt = Template('''Provide an expert analysis on the major segments of costs of the company $ticker. Cost segments include, but are not limited to natural resources, specific parts, considerable energy consumption, computing power, cloud usage, etc,. Explain in Korean.''')

customer_analysis_prompt = Template('''Based on the text you have generated, provide an expert analysis on the persona for the customer of $ticker. List possible segments of the customers. Among each possible candidates, eleborate the details about customers; who are they, why they pay for the $ticker`s product, etc,. Write in Korean. ''')
