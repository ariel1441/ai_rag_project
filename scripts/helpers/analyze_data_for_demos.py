"""
Analyze Request.csv data and create demo questions with expected results.
"""
import pandas as pd
import json
from pathlib import Path

# Load data
print("Loading data...")
df = pd.read_csv('data/raw/request.csv', low_memory=False)
print(f"Loaded {len(df)} requests")

# Analyze key fields
print("\n=== Analysis ===")

# People
print("\nTop people (UpdatedBy):")
top_updated_by = df['UpdatedBy'].value_counts().head(15).to_dict()
print(top_updated_by)

print("\nTop people (CreatedBy):")
top_created_by = df['CreatedBy'].value_counts().head(15).to_dict()
print(top_created_by)

# Projects
print("\nTop projects:")
top_projects = df['ProjectName'].value_counts().head(20).to_dict()
print(top_projects)

# Types
print("\nRequest types:")
types = df['RequestTypeId'].value_counts().to_dict()
print(types)

# Status
print("\nRequest status:")
status = df['RequestStatusId'].value_counts().to_dict()
print(status)

# Create demo questions with expected results
demo_questions = []

# Question 1: Person query - יניב ליבוביץ
print("\n=== Creating Demo Questions ===")
person_name = "יניב ליבוביץ"
person_results = df[df['UpdatedBy'].str.contains(person_name, na=False, case=False) | 
                    df['CreatedBy'].str.contains(person_name, na=False, case=False) |
                    df['ResponsibleEmployeeName'].str.contains(person_name, na=False, case=False)]
print(f"\nQuestion 1: פניות מ{person_name}")
print(f"Expected: {len(person_results)} requests")
print(f"Sample IDs: {person_results['RequestId'].head(10).tolist()}")

demo_questions.append({
    'question': f'פניות מ{person_name}',
    'question_english': f'Requests from {person_name}',
    'expected_count': len(person_results),
    'sample_ids': person_results['RequestId'].head(10).tolist(),
    'type': 'person',
    'entity': person_name
})

# Question 2: Another person - אור גלילי
person_name2 = "אור גלילי"
person_results2 = df[df['UpdatedBy'].str.contains(person_name2, na=False, case=False) | 
                     df['CreatedBy'].str.contains(person_name2, na=False, case=False) |
                     df['ResponsibleEmployeeName'].str.contains(person_name2, na=False, case=False) |
                     df['ProjectName'].str.contains(person_name2, na=False, case=False)]
print(f"\nQuestion 2: פניות מא{person_name2}")
print(f"Expected: {len(person_results2)} requests")
print(f"Sample IDs: {person_results2['RequestId'].head(10).tolist()}")

demo_questions.append({
    'question': f'פניות מא{person_name2}',
    'question_english': f'Requests from {person_name2}',
    'expected_count': len(person_results2),
    'sample_ids': person_results2['RequestId'].head(10).tolist(),
    'type': 'person',
    'entity': person_name2
})

# Question 3: Count query
print(f"\nQuestion 3: כמה פניות יש מ{person_name}?")
demo_questions.append({
    'question': f'כמה פניות יש מ{person_name}?',
    'question_english': f'How many requests are from {person_name}?',
    'expected_count': len(person_results),
    'expected_answer': f'נמצאו {len(person_results)} פניות של {person_name}',
    'type': 'count',
    'entity': person_name
})

# Question 4: Project query
project_name = "בדיקה אור גלילי"
project_results = df[df['ProjectName'].str.contains(project_name, na=False, case=False)]
print(f"\nQuestion 4: פרויקט {project_name}")
print(f"Expected: {len(project_results)} requests")
print(f"Sample IDs: {project_results['RequestId'].head(10).tolist()}")

demo_questions.append({
    'question': f'פרויקט {project_name}',
    'question_english': f'Project {project_name}',
    'expected_count': len(project_results),
    'sample_ids': project_results['RequestId'].head(10).tolist(),
    'type': 'project',
    'entity': project_name
})

# Question 5: Type query
type_id = 4
type_results = df[df['RequestTypeId'] == type_id]
print(f"\nQuestion 5: בקשות מסוג {type_id}")
print(f"Expected: {len(type_results)} requests")
print(f"Sample IDs: {type_results['RequestId'].head(10).tolist()}")

demo_questions.append({
    'question': f'בקשות מסוג {type_id}',
    'question_english': f'Requests of type {type_id}',
    'expected_count': len(type_results),
    'sample_ids': type_results['RequestId'].head(10).tolist(),
    'type': 'type',
    'entity': str(type_id)
})

# Question 6: Status query
status_id = 10
status_results = df[df['RequestStatusId'] == status_id]
print(f"\nQuestion 6: בקשות בסטטוס {status_id}")
print(f"Expected: {len(status_results)} requests")

demo_questions.append({
    'question': f'בקשות בסטטוס {status_id}',
    'question_english': f'Requests with status {status_id}',
    'expected_count': len(status_results),
    'sample_ids': status_results['RequestId'].head(10).tolist(),
    'type': 'status',
    'entity': str(status_id)
})

# Question 7: General semantic query
general_term = "תיאום תכנון"
general_results = df[df['ProjectName'].str.contains(general_term, na=False, case=False) |
                     df['ProjectDesc'].str.contains(general_term, na=False, case=False) |
                     df['AreaDesc'].str.contains(general_term, na=False, case=False)]
print(f"\nQuestion 7: {general_term}")
print(f"Expected: {len(general_results)} requests (semantic search)")

demo_questions.append({
    'question': general_term,
    'question_english': 'Planning coordination',
    'expected_count': len(general_results),
    'sample_ids': general_results['RequestId'].head(10).tolist(),
    'type': 'general',
    'entity': general_term
})

# Question 8: אוקסנה כלפון
person_name3 = "אוקסנה כלפון"
person_results3 = df[df['UpdatedBy'].str.contains(person_name3, na=False, case=False) | 
                     df['CreatedBy'].str.contains(person_name3, na=False, case=False) |
                     df['ResponsibleEmployeeName'].str.contains(person_name3, na=False, case=False)]
print(f"\nQuestion 8: פניות מא{person_name3}")
print(f"Expected: {len(person_results3)} requests")

demo_questions.append({
    'question': f'פניות מא{person_name3}',
    'question_english': f'Requests from {person_name3}',
    'expected_count': len(person_results3),
    'sample_ids': person_results3['RequestId'].head(10).tolist(),
    'type': 'person',
    'entity': person_name3
})

# Question 9: משה אוגלבו
person_name4 = "משה אוגלבו"
person_results4 = df[df['UpdatedBy'].str.contains(person_name4, na=False, case=False) | 
                     df['CreatedBy'].str.contains(person_name4, na=False, case=False) |
                     df['ResponsibleEmployeeName'].str.contains(person_name4, na=False, case=False)]
print(f"\nQuestion 9: פניות מ{person_name4}")
print(f"Expected: {len(person_results4)} requests")

demo_questions.append({
    'question': f'פניות מ{person_name4}',
    'question_english': f'Requests from {person_name4}',
    'expected_count': len(person_results4),
    'sample_ids': person_results4['RequestId'].head(10).tolist(),
    'type': 'person',
    'entity': person_name4
})

# Question 10: Complex query
print(f"\nQuestion 10: כמה פניות יש מסוג {type_id} בסטטוס {status_id}?")
complex_results = df[(df['RequestTypeId'] == type_id) & (df['RequestStatusId'] == status_id)]
print(f"Expected: {len(complex_results)} requests")

demo_questions.append({
    'question': f'כמה פניות יש מסוג {type_id} בסטטוס {status_id}?',
    'question_english': f'How many requests of type {type_id} with status {status_id}?',
    'expected_count': len(complex_results),
    'sample_ids': complex_results['RequestId'].head(10).tolist(),
    'type': 'complex',
    'entity': f'type_{type_id}_status_{status_id}'
})

# Save to JSON
output_file = Path('DEMO_QUESTIONS_AND_EXPECTED_RESULTS.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(demo_questions, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved {len(demo_questions)} demo questions to {output_file}")

# Print summary
print("\n=== Summary ===")
for i, q in enumerate(demo_questions, 1):
    print(f"{i}. {q['question']} ({q['question_english']})")
    print(f"   Type: {q['type']}, Expected: {q['expected_count']} requests")

