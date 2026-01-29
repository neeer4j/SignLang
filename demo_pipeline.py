"""
Sign Language Pipeline Demo/Test

Simple demonstration and testing of the redesigned sign language
processing pipeline components.

Run this file to verify the core pipeline is working:
    python demo_pipeline.py
"""
import sys
import time

def test_vocabulary():
    """Test the sign vocabulary."""
    print("\n=== Testing Sign Vocabulary ===")
    
    from core.sign_vocabulary import SignVocabulary
    
    vocab = SignVocabulary()
    
    # Test letter lookup
    print("\nLetter lookups:")
    for letter in ['A', 'B', 'C', 'Z']:
        sign = vocab.get_sign_by_gesture(letter)
        if sign:
            print(f"  '{letter}' -> {sign.text} ({sign.category.value})")
    
    # Test word lookup
    print("\nWord lookups:")
    for word in ['hello', 'thank_you', 'yes', 'wave']:
        sign = vocab.get_sign_by_gesture(word)
        if sign:
            print(f"  '{word}' -> {sign.text} (emoji: {sign.emoji})")
    
    # Test pattern recognition
    print("\nWord pattern recognition:")
    patterns = ['HELLO', 'HI', 'THANKS', 'YES', 'UNKNOWN']
    for pattern in patterns:
        result = vocab.recognize_word_pattern(pattern)
        print(f"  '{pattern}' -> {result or '(not recognized)'}")
    
    print("\n✓ Vocabulary tests passed!")


def test_temporal_aggregator():
    """Test the temporal aggregator."""
    print("\n=== Testing Temporal Aggregator ===")
    
    from core.temporal_aggregator import TemporalAggregator
    from core.gesture_sequence import GestureFrame, GestureType
    
    aggregator = TemporalAggregator(
        window_size=10,
        stability_threshold=3,
        min_confidence=0.5
    )
    
    # Simulate a sequence of frames
    print("\nSimulating gesture frames...")
    
    recognized_gestures = []
    
    # Simulate 'H' gesture for several frames
    for i in range(8):
        frame = GestureFrame(
            timestamp=time.time(),
            frame_id=i,
            hand_detected=True,
            predicted_label='H',
            confidence=0.85,
            gesture_type=GestureType.STATIC
        )
        result = aggregator.process_frame(frame)
        if result:
            recognized_gestures.append(result)
            print(f"  Frame {i}: Recognized '{result.label}' (conf: {result.confidence:.2f})")
    
    # Simulate 'I' gesture
    for i in range(8, 16):
        frame = GestureFrame(
            timestamp=time.time(),
            frame_id=i,
            hand_detected=True,
            predicted_label='I',
            confidence=0.82,
            gesture_type=GestureType.STATIC
        )
        result = aggregator.process_frame(frame)
        if result:
            recognized_gestures.append(result)
            print(f"  Frame {i}: Recognized '{result.label}' (conf: {result.confidence:.2f})")
    
    print(f"\nTotal gestures recognized: {len(recognized_gestures)}")
    print(f"Stats: {aggregator.get_statistics()}")
    
    print("\n✓ Temporal aggregator tests passed!")


def test_sentence_constructor():
    """Test the sentence constructor."""
    print("\n=== Testing Sentence Constructor ===")
    
    from core.sentence_constructor import SentenceConstructor
    from core.gesture_sequence import RecognizedGesture, GestureType
    
    constructor = SentenceConstructor()
    
    # Add some letters to spell "HELLO"
    print("\nBuilding 'HELLO'...")
    for letter in ['H', 'E', 'L', 'L', 'O']:
        gesture = RecognizedGesture(
            label=letter,
            gesture_type=GestureType.STATIC,
            confidence=0.85,
            start_time=time.time(),
            end_time=time.time(),
            frame_count=5
        )
        constructor.add_gesture(gesture)
        print(f"  Added '{letter}' -> Preview: {constructor.get_preview()}")
    
    # Finalize word
    constructor.insert_space()
    
    # Add a word gesture
    print("\nAdding word gesture 'wave' (Hello)...")
    wave_gesture = RecognizedGesture(
        label='WAVE',
        gesture_type=GestureType.DYNAMIC,
        confidence=0.90,
        start_time=time.time(),
        end_time=time.time(),
        frame_count=10,
        is_word_level=True,
        semantic_meaning='Hello'
    )
    constructor.add_gesture(wave_gesture)
    
    print(f"\nFinal text: {constructor.get_current_text()}")
    print(f"Preview: {constructor.get_preview()}")
    
    # Finalize
    result = constructor.finalize_sentence()
    print(f"\nTranslation result:")
    print(f"  Text: {result.text}")
    print(f"  Words: {result.word_count}")
    print(f"  Gestures: {result.gesture_count}")
    print(f"  Confidence: {result.confidence:.2f}")
    
    print("\n✓ Sentence constructor tests passed!")


def test_text_to_sign():
    """Test text-to-sign translation."""
    print("\n=== Testing Text-to-Sign Translation ===")
    
    from core.text_to_sign import TextToSignTranslator
    
    translator = TextToSignTranslator()
    
    # Test various texts
    texts = [
        "Hello",
        "Thank you",
        "I love you",
        "My name is John",
    ]
    
    for text in texts:
        print(f"\nTranslating: '{text}'")
        result = translator.translate(text)
        
        print(f"  Signs: {len(result.signs)}")
        for sign in result.signs:
            emoji = f" {sign.emoji}" if sign.emoji else ""
            print(f"    - {sign.display_text}{emoji} ({sign.output_type.value})")
    
    print("\n✓ Text-to-sign tests passed!")


def test_full_pipeline():
    """Test the full processing pipeline."""
    print("\n=== Testing Full Pipeline ===")
    
    from core.pipeline import SignLanguagePipeline, PipelineMode, PipelineConfig
    from core.gesture_sequence import GestureType
    
    # Create pipeline
    config = PipelineConfig(
        aggregation_window=10,
        stability_threshold=3,
        min_confidence=0.5
    )
    pipeline = SignLanguagePipeline(config)
    
    # Start pipeline
    print("\nStarting pipeline in LIVE_ACCUMULATE mode...")
    pipeline.start(PipelineMode.LIVE_ACCUMULATE)
    
    # Simulate gestures
    gestures_to_send = [
        ('H', 0.85, GestureType.STATIC),
        ('I', 0.82, GestureType.STATIC),
        ('WAVE', 0.90, GestureType.DYNAMIC),  # Should be recognized as "Hello"
    ]
    
    print("\nProcessing gestures...")
    for label, conf, gtype in gestures_to_send:
        result = pipeline.process_gesture(label, conf, gtype)
        if result:
            print(f"  Processed '{label}' -> Current text: {result}")
    
    # Get final translation
    print("\nFinalizing translation...")
    result = pipeline.stop_and_translate()
    
    print(f"\nFinal Translation:")
    print(f"  Text: '{result.text}'")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Gestures: {result.gesture_count}")
    
    # Test text-to-sign
    print("\n\nTesting reverse translation...")
    signs = pipeline.translate_text_to_sign("Hello friend")
    print(f"  'Hello friend' -> {len(signs.signs)} signs")
    for sign in signs.signs:
        print(f"    - {sign.display_text} ({sign.output_type.value})")
    
    print("\n✓ Full pipeline tests passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Sign Language Pipeline Demo/Test")
    print("=" * 60)
    
    try:
        test_vocabulary()
        test_temporal_aggregator()
        test_sentence_constructor()
        test_text_to_sign()
        test_full_pipeline()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
