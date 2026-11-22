from services.reply_triage.classifier import reply_classifier

def test_classify_interested_reply():
    res = reply_classifier.classify_reply("Re: Scaling pipelines", "Yes, let's schedule a 15-min demo next Tuesday.")
    assert res["intent"] == "interested"
    assert res["confidence"] >= 0.90
    assert "meeting" in res["suggested_action"].lower()

def test_classify_unsubscribe_reply():
    res = reply_classifier.classify_reply("Re: Demo", "Please remove me from this list immediately.")
    assert res["intent"] == "unsubscribe"
    assert res["confidence"] >= 0.95

def test_classify_out_of_office_reply():
    res = reply_classifier.classify_reply("Automatic reply", "I am out of the office traveling with limited email access.")
    assert res["intent"] == "out_of_office"
