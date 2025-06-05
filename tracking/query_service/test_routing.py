#!/usr/bin/env python3
"""
Test script for the improved agent routing logic.
"""

from intent_classifier import intent_classifier, QueryIntent

def test_routing_examples():
    """Test various query examples to verify routing improvements."""
    
    test_queries = [
        # Data retrieval queries (should go to Librarian Agent)
        "is there any evidence of shoplifting",
        "show me what happened at 2:30 PM",
        "find all instances of person wearing red shirt",
        "detect any suspicious behavior",
        "who was in the room during the incident",
        "where did the theft occur",
        "search for audio mentioning money",
        "identify the person in frame 123",
        
        # Conversation history queries (should go to Memory Agent)
        "what did we discuss earlier",
        "recall our previous conversation",
        "what was mentioned before about security",
        "remember what was said about the incident",
        "previous discussions about this topic",
        
        # General questions (should go to Quick Answer Agent)
        "hello how are you",
        "what are your capabilities",
        "how does this system work",
        "can you help me",
        "what features do you have",
        
        # Unclear queries (should go to Query Optimization Agent)
        "um",
        "stuff",
        "something about things",
        "???",
        "help with that thing"
    ]
    
    print("🧪 Testing Improved Agent Routing Logic")
    print("=" * 60)
    
    routing_results = {}
    
    for query in test_queries:
        recommendation = intent_classifier.get_routing_recommendation(query)
        routing_results[query] = recommendation
        
        print(f"\n📝 Query: '{query}'")
        print(f"🎯 Recommended Agent: {recommendation['recommended_agent']}")
        print(f"🧠 Primary Intent: {recommendation['primary_intent']}")
        print(f"📊 Confidence: {recommendation['confidence']:.2f}")
        print(f"💭 Reasoning: {recommendation['reasoning']}")
        
        if recommendation['should_fallback']:
            print("⚠️  Low confidence - may need fallback handling")
    
    # Summary analysis
    print("\n" + "=" * 60)
    print("📊 ROUTING SUMMARY")
    print("=" * 60)
    
    agent_counts = {}
    for query, result in routing_results.items():
        agent = result['recommended_agent']
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
    
    for agent, count in sorted(agent_counts.items()):
        print(f"{agent}: {count} queries")
    
    # Test specific problematic query from the logs
    print("\n" + "=" * 60)
    print("🔍 SPECIFIC TEST: Shoplifting Query")
    print("=" * 60)
    
    shoplifting_query = "is there any evidence of shoplifting"
    result = intent_classifier.get_routing_recommendation(shoplifting_query)
    
    print(f"Query: '{shoplifting_query}'")
    print(f"Recommended Agent: {result['recommended_agent']}")
    print(f"Expected: Librarian Agent")
    print(f"✅ Correct!" if result['recommended_agent'] == "Librarian Agent" else "❌ Incorrect!")
    
    return routing_results

def test_intent_classification():
    """Test the intent classification specifically."""
    print("\n" + "=" * 60)
    print("🧠 INTENT CLASSIFICATION TESTS")
    print("=" * 60)
    
    test_cases = [
        ("find evidence of theft", QueryIntent.DATA_RETRIEVAL),
        ("what did we talk about before", QueryIntent.CONVERSATION_HISTORY),
        ("hello there", QueryIntent.GENERAL_QUESTION),
        ("um what", QueryIntent.UNCLEAR_QUERY)
    ]
    
    for query, expected_intent in test_cases:
        intent, confidence, scores = intent_classifier.classify_intent(query)
        print(f"\nQuery: '{query}'")
        print(f"Detected: {intent.value} (confidence: {confidence:.2f})")
        print(f"Expected: {expected_intent.value}")
        print(f"✅ Correct!" if intent == expected_intent else "❌ Incorrect!")
        print(f"All scores: {scores}")

if __name__ == "__main__":
    try:
        routing_results = test_routing_examples()
        test_intent_classification()
        
        print("\n" + "=" * 60)
        print("✅ Routing tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        import traceback
        traceback.print_exc() 