#!/usr/bin/env python3
"""
Quick test to demonstrate routing improvements without OpenAI API
"""

from intent_classifier import intent_classifier

def test_critical_query():
    """Test the problematic query from the logs"""
    print('🧪 TESTING ROUTING IMPROVEMENTS')
    print('=' * 50)
    
    # Test the problematic query from your logs
    test_query = 'is there any evidence of shoplifting'
    print(f'Query: "{test_query}"')
    print()

    result = intent_classifier.get_routing_recommendation(test_query)
    print(f'🎯 Recommended Agent: {result["recommended_agent"]}')
    print(f'🧠 Primary Intent: {result["primary_intent"]}')
    print(f'📊 Confidence: {result["confidence"]:.2f}')
    print(f'💭 Reasoning: {result["reasoning"]}')
    print()

    if result['recommended_agent'] == 'Librarian Agent':
        print('✅ SUCCESS: Query now correctly routes to Librarian Agent!')
        print('   This fixes the issue where it was going to Quick Answer Agent')
    else:
        print('❌ ISSUE: Query not routing to expected Librarian Agent')

    print()
    print('🔄 BEFORE vs AFTER:')
    print('Before: Quick Answer Agent → Generic response about shoplifting')
    print('After:  Librarian Agent → Search for actual evidence in data')
    print()

def test_multiple_scenarios():
    """Test various query scenarios"""
    print('🔍 TESTING VARIOUS SCENARIOS')
    print('=' * 50)
    
    test_cases = [
        ("is there any evidence of shoplifting", "Librarian Agent", "Data retrieval"),
        ("what did we discuss earlier", "Memory Agent", "Conversation history"),
        ("hello how are you", "Quick Answer Agent", "General greeting"),
        ("find person in red shirt", "Librarian Agent", "Visual search"),
        ("um what", "Query Optimization Agent", "Unclear query")
    ]
    
    success_count = 0
    
    for query, expected_agent, description in test_cases:
        result = intent_classifier.get_routing_recommendation(query)
        actual_agent = result["recommended_agent"]
        
        success = actual_agent == expected_agent
        success_count += 1 if success else 0
        
        status = "✅" if success else "❌"
        print(f'{status} "{query}"')
        print(f'   Expected: {expected_agent} | Got: {actual_agent}')
        print(f'   {description} (confidence: {result["confidence"]:.2f})')
        print()
    
    print(f'📊 OVERALL RESULTS: {success_count}/{len(test_cases)} tests passed')
    accuracy = (success_count / len(test_cases)) * 100
    print(f'🎯 Accuracy: {accuracy:.1f}%')

if __name__ == "__main__":
    test_critical_query()
    print()
    test_multiple_scenarios() 