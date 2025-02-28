import re
from typing import Dict, List, Any
import html2text

class ResponseGenerator:
    def __init__(self):
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.ignore_tables = False
        
    def extract_steps(self, text):
        """Extract steps or numbered instructions from text"""
        # Look for numbered steps
        step_pattern = r'(\d+\.\s+.*?(?=\d+\.\s+|$))'
        steps = re.findall(step_pattern, text, re.DOTALL)
        
        if steps:
            return steps
        
        # Look for bullet points
        bullet_pattern = r'(\*\s+.*?(?=\*\s+|$))'
        bullets = re.findall(bullet_pattern, text, re.DOTALL)
        
        if bullets:
            return bullets
        
        # Split by sentences if no steps or bullets found
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        return sentences[:5]  # Limit to 5 sentences
    
    def clean_text(self, text):
        """Clean up the text from markdown artifacts"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove markdown links but keep the text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        return text
    
    def format_how_to_response(self, query_result):
        """Format a response for a how-to query"""
        if query_result['type'] == 'not_how_to':
            return query_result['message']
        
        if query_result['type'] == 'no_results':
            return query_result['message']
        
        results = query_result['results']
        cdp_name = query_result['cdp'] or "the CDP"
        
        # Get the best result
        best_result = results[0]
        
        # Convert HTML to Markdown if needed
        if 'html' in best_result:
            content = self.h2t.handle(best_result['html'])
        else:
            content = best_result['chunk_text']
        
        # Clean the text
        content = self.clean_text(content)
        
        # Extract steps or relevant sections
        steps = self.extract_steps(content)
        
        # Build response
        response = f"Here's how to {query_result['query'].lower().replace('how do i', '').replace('how to', '').strip()} in {cdp_name.capitalize()}:\n\n"
        
        if steps:
            for i, step in enumerate(steps, 1):
                # Clean up each step
                step = self.clean_text(step)
                # If it doesn't start with a number, add one
                if not re.match(r'^\d+\.', step):
                    response += f"{i}. {step}\n"
                else:
                    response += f"{step}\n"
        else:
            response += content
        
        response += f"\n\nFor more details, you can check the documentation at: {best_result['url']}"
        
        return response
    
    def format_comparison_response(self, comparison_result):
        """Format a response for a CDP comparison query"""
        if comparison_result['type'] == 'comparison_error':
            return comparison_result['message']
        
        feature = comparison_result['feature']
        cdps = comparison_result['cdps']
        data = comparison_result['comparison_data']
        
        response = f"Here's a comparison of {feature} between {' and '.join(cdp.capitalize() for cdp in cdps)}:\n\n"
        
        for cdp in cdps:
            if cdp in data:
                best_result = data[cdp][0]
                
                # Convert HTML to Markdown if needed
                if 'html' in best_result:
                    content = self.h2t.handle(best_result['html'])
                else:
                    content = best_result['chunk_text']
                
                # Clean the text
                content = self.clean_text(content)
                
                # Extract key points (first 3 sentences)
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content) if s.strip()]
                key_points = sentences[:3]
                
                response += f"**{cdp.capitalize()}**:\n"
                for point in key_points:
                    response += f"- {point}\n"
                
                response += f"More details: {best_result['url']}\n\n"
            else:
                response += f"**{cdp.capitalize()}**: I couldn't find specific information about {feature} for this CDP.\n\n"
        
        response += "Note: This comparison is based on the available documentation and may not cover all aspects of the feature."
        
        return response
    
    def generate_response(self, query, result):
        """Generate a response based on the query and search results"""
        if isinstance(result, dict) and 'type' in result:
            if result['type'] in ['not_how_to', 'no_results']:
                return self.format_how_to_response(result)
            elif result['type'] == 'results':
                return self.format_how_to_response(result)
            elif result['type'] in ['comparison', 'comparison_error']:
                return self.format_comparison_response(result)
        
        # Fallback response
        return "I'm sorry, I couldn't process your question. Please try asking a how-to question about Segment, mParticle, Lytics, or Zeotap."

# Usage example
def generate_response_example(query_result):
    generator = ResponseGenerator()
    response = generator.generate_response("How do I set up a new source in Segment?", query_result)
    return response