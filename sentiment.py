from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch


class SentimentAnalyzer:
    def __init__(self, model_name="distilbert-base-uncased-finetuned-sst-2-english"):
        """
        یک تحلیل‌گر احساسات مبتنی بر مدل BERT
        که با نسخه‌های جدید PyTorch و Transformers سازگاره
        """

        if torch.cuda.is_available():
            device = 0  
        else:
            device = -1  

        print(f"✅ Sentiment model is loading on {'GPU' if device == 0 else 'CPU'}...")


        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)

        self.classifier = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=tokenizer,
            device=device,
            truncation=True,
            trust_remote_code=True
        )

    def analyze(self, text):
        """
        متن ورودی رو تحلیل می‌کنه و نتیجه‌ی احساس (مثلاً POSITIVE / NEGATIVE) رو برمی‌گردونه.
        """
        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.0}


        result = self.classifier(text)[0]


        return {
            "label": result["label"],
            "score": round(float(result["score"]), 4)
        }


if __name__ == "__main__":
    sa = SentimentAnalyzer()
    text = "I really loved this movie, it was fantastic!"
    print(sa.analyze(text))
