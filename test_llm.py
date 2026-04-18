from services.summarizer import summarize_meeting
from services.task_extractor import extract_tasks


text1 = """
[Merve | 00:00:01 - 00:00:10]
Frontend teslimini cuma gününe çekelim.

[Ahmet | 00:00:11 - 00:00:20]
Ben testleri perşembe akşamına kadar tamamlarım.
"""

text2 = """
[Merve | 00:00:01 - 00:00:10]
Bugün genel durum değerlendirmesi yaptık.

[Ahmet | 00:00:11 - 00:00:20]
Her şey planlandığı gibi ilerliyor.
"""

print("=== TEST 1 ===")
print("SUMMARY:")
print(summarize_meeting(text1))
print("\nTASKS:")
print(extract_tasks(text1))

print("\n=== TEST 2 ===")
print("SUMMARY:")
print(summarize_meeting(text2))
print("\nTASKS:")
print(extract_tasks(text2))
