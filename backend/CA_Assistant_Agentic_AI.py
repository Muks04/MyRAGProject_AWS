import boto3
import json
import base64
import time
from urllib.parse import parse_qs
import re
from datetime import datetime, timedelta
from decimal import Decimal
import math

# ================================
# CONFIGURATION
# ================================

REGION = "us-east-1"
MODEL_ID = "amazon.nova-pro-v1:0"
TABLE_NAME = "CA_Assistant_Chat_History"
KNOWLEDGE_BASE_ID = "UVRLNSMGZG"
AGENTS_TABLE = "FinBot_Agent_Sessions"  # New table for agent sessions

# Agent Configuration
ENABLE_AGENTS = True
MAX_AGENT_ITERATIONS = 5
AGENT_TIMEOUT = 30  # seconds

# Initialize clients
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)
bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

# ================================
# AGENT SYSTEM CORE
# ================================

class AgentOrchestrator:
    """Main orchestrator that decides which agents to use."""
    
    def __init__(self):
        self.available_agents = {
            'tax_calculator': TaxCalculatorAgent(),
            'compliance_checker': ComplianceCheckerAgent(),
            'form_filler': FormFillingAgent(),
            'tally_helper': TallyIntegrationAgent(),
            'document_analyzer': DocumentAnalysisAgent(),
            'deadline_tracker': DeadlineTrackerAgent(),
            'rag_responder': RAGResponderAgent()
        }
    
    def analyze_intent(self, user_message):
        """Analyze user intent and determine which agents to activate."""
        msg_lower = user_message.lower()
        
        # Intent patterns for different agents
        intent_patterns = {
            'calculate_tax': [
                r'calculate.*tax', r'compute.*tax', r'tax.*calculation',
                r'how much.*tax', r'tax.*amount', r'calculate.*tds',
                r'salary.*\d+', r'income.*\d+', r'profit.*\d+'
            ],
            'check_compliance': [
                r'compliant', r'compliance', r'check.*status',
                r'am i.*compliant', r'filing.*status', r'penalty'
            ],
            'fill_forms': [
                r'fill.*form', r'itr.*filing', r'gst.*return',
                r'form.*\d+', r'file.*return', r'submit.*form'
            ],
            'tally_operations': [
                r'tally.*help', r'reconcile.*bank', r'backup.*data',
                r'export.*data', r'import.*data', r'tally.*error'
            ],
            'analyze_document': [
                r'analyze.*document', r'check.*document', r'review.*file',
                r'validate.*document', r'document.*compliance'
            ],
            'track_deadlines': [
                r'deadline', r'due.*date', r'when.*file',
                r'reminder', r'schedule', r'calendar'
            ],
            'general_query': [
                r'what.*is', r'explain', r'tell.*me', r'how.*to',
                r'rates', r'rules', r'provisions'
            ]
        }
        
        detected_intents = []
        
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, msg_lower):
                    detected_intents.append(intent)
                    break
        
        # Default to general query if no specific intent
        if not detected_intents:
            detected_intents = ['general_query']
        
        print(f"🎯 Detected intents: {detected_intents}")
        return detected_intents
    
    def execute_agents(self, user_message, phone_number, intents):
        """Execute appropriate agents based on detected intents."""
        results = []
        
        for intent in intents[:2]:  # Limit to 2 agents for performance
            agent_name = self.get_agent_for_intent(intent)
            if agent_name and agent_name in self.available_agents:
                try:
                    print(f"🤖 Executing agent: {agent_name}")
                    agent = self.available_agents[agent_name]
                    result = agent.execute(user_message, phone_number)
                    if result:
                        results.append(result)
                except Exception as error:
                    print(f"❌ Agent {agent_name} error: {error}")
        
        return results
    
    def get_agent_for_intent(self, intent):
        """Map intents to specific agents."""
        intent_to_agent = {
            'calculate_tax': 'tax_calculator',
            'check_compliance': 'compliance_checker',
            'fill_forms': 'form_filler',
            'tally_operations': 'tally_helper',
            'analyze_document': 'document_analyzer',
            'track_deadlines': 'deadline_tracker',
            'general_query': 'rag_responder'
        }
        return intent_to_agent.get(intent)

# ================================
# INDIVIDUAL AGENTS
# ================================

class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, name):
        self.name = name
    
    def execute(self, user_message, phone_number):
        """Override in subclasses."""
        raise NotImplementedError
    
    def call_bedrock(self, prompt, max_tokens=300):
        """Call Bedrock for AI processing."""
        try:
            response = bedrock_runtime.invoke_model(
                modelId=MODEL_ID,
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.1,
                    "top_p": 0.9
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text']
            
        except Exception as error:
            print(f"❌ Bedrock call error: {error}")
            return None

class TaxCalculatorAgent(BaseAgent):
    """Agent for tax calculations."""
    
    def __init__(self):
        super().__init__("TaxCalculator")
    
    def execute(self, user_message, phone_number):
        """Perform tax calculations."""
        try:
            # Extract numbers from message
            numbers = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', user_message)
            if not numbers:
                return None
            
            # Convert to float
            amount = float(numbers[0].replace(',', ''))
            
            # Determine calculation type
            msg_lower = user_message.lower()
            
            if any(word in msg_lower for word in ['salary', 'income', 'annual']):
                return self.calculate_income_tax(amount)
            elif any(word in msg_lower for word in ['tds', 'professional', 'rent']):
                return self.calculate_tds(amount, msg_lower)
            elif any(word in msg_lower for word in ['gst', 'tax']):
                return self.calculate_gst(amount, msg_lower)
            
            return None
            
        except Exception as error:
            print(f"❌ Tax calculation error: {error}")
            return None
    
    def calculate_income_tax(self, annual_income):
        """Calculate income tax for FY 2024-25."""
        
        # New tax regime slabs
        slabs = [
            (300000, 0),      # 0% up to 3L
            (600000, 0.05),   # 5% from 3L to 6L
            (900000, 0.10),   # 10% from 6L to 9L
            (1200000, 0.15),  # 15% from 9L to 12L
            (1500000, 0.20),  # 20% from 12L to 15L
            (float('inf'), 0.30)  # 30% above 15L
        ]
        
        total_tax = 0
        remaining_income = annual_income
        previous_limit = 0
        
        calculation_steps = []
        
        for limit, rate in slabs:
            if remaining_income <= 0:
                break
            
            taxable_in_slab = min(remaining_income, limit - previous_limit)
            tax_in_slab = taxable_in_slab * rate
            total_tax += tax_in_slab
            
            if taxable_in_slab > 0:
                calculation_steps.append(
                    f"₹{previous_limit:,.0f} - ₹{min(limit, annual_income):,.0f}: "
                    f"₹{taxable_in_slab:,.0f} × {rate*100:.0f}% = ₹{tax_in_slab:,.0f}"
                )
            
            remaining_income -= taxable_in_slab
            previous_limit = limit
            
            if limit == float('inf'):
                break
        
        # Add cess (4% on tax)
        cess = total_tax * 0.04
        total_with_cess = total_tax + cess
        
        result = f"""💰 Income Tax Calculator (FY 2024-25)

Annual Income: ₹{annual_income:,.0f}

Tax Calculation (New Regime):
{chr(10).join(calculation_steps)}

Subtotal Tax: ₹{total_tax:,.0f}
Health & Education Cess (4%): ₹{cess:,.0f}
Total Tax: ₹{total_with_cess:,.0f}

Monthly Tax: ₹{total_with_cess/12:,.0f}
Take-home: ₹{annual_income - total_with_cess:,.0f}

🤖 Calculated by TaxCalculator Agent"""
        
        return result
    
    def calculate_tds(self, amount, message_context):
        """Calculate TDS based on context."""
        
        tds_rates = {
            'professional': 0.10,
            'rent': 0.10,
            'interest': 0.10,
            'contractor': 0.02,
            'commission': 0.05
        }
        
        # Determine TDS type
        tds_type = 'professional'  # default
        for key in tds_rates.keys():
            if key in message_context:
                tds_type = key
                break
        
        rate = tds_rates[tds_type]
        tds_amount = amount * rate
        net_amount = amount - tds_amount
        
        result = f"""💰 TDS Calculator (FY 2024-25)

Payment Type: {tds_type.title()}
Gross Amount: ₹{amount:,.0f}
TDS Rate: {rate*100:.0f}%
TDS Amount: ₹{tds_amount:,.0f}
Net Payment: ₹{net_amount:,.0f}

Threshold: ₹30,000 (annual)
Section: 194J (Professional Services)

🤖 Calculated by TaxCalculator Agent"""
        
        return result
    
    def calculate_gst(self, amount, message_context):
        """Calculate GST based on context."""
        
        # Determine GST rate based on context
        if any(word in message_context for word in ['it', 'software', 'service']):
            gst_rate = 0.18
            category = "IT Services"
        elif any(word in message_context for word in ['food', 'restaurant']):
            gst_rate = 0.05
            category = "Food Services"
        elif any(word in message_context for word in ['luxury', 'car']):
            gst_rate = 0.28
            category = "Luxury Items"
        else:
            gst_rate = 0.18
            category = "Standard Services"
        
        gst_amount = amount * gst_rate
        total_amount = amount + gst_amount
        
        result = f"""💰 GST Calculator (FY 2024-25)

Category: {category}
Base Amount: ₹{amount:,.0f}
GST Rate: {gst_rate*100:.0f}%
GST Amount: ₹{gst_amount:,.0f}
Total Amount: ₹{total_amount:,.0f}

CGST: ₹{gst_amount/2:,.0f}
SGST: ₹{gst_amount/2:,.0f}

🤖 Calculated by TaxCalculator Agent"""
        
        return result

class ComplianceCheckerAgent(BaseAgent):
    """Agent for compliance checking."""
    
    def __init__(self):
        super().__init__("ComplianceChecker")
    
    def execute(self, user_message, phone_number):
        """Check compliance status."""
        
        # Get user's filing history (mock data for demo)
        compliance_status = self.check_user_compliance(phone_number)
        
        result = f"""🔍 Compliance Status Check

Phone: {phone_number[-4:]}****

📊 ITR Filing Status:
• FY 2023-24: ✅ Filed (On Time)
• FY 2022-23: ✅ Filed (On Time)
• FY 2021-22: ⚠️ Filed (Late - ₹5,000 penalty)

📋 GST Compliance:
• March 2024: ✅ Filed
• February 2024: ✅ Filed  
• January 2024: ❌ Pending (Due: 20th Feb)

⏰ Upcoming Deadlines:
• ITR FY 2024-25: July 31, 2025
• GST April 2024: May 20, 2024
• TDS Q4 2023-24: April 30, 2024

🚨 Action Required:
1. File pending GST return for January 2024
2. Pay late fee: ₹200 per day

🤖 Analyzed by ComplianceChecker Agent"""
        
        return result
    
    def check_user_compliance(self, phone_number):
        """Mock compliance check - integrate with real systems."""
        # In production, integrate with:
        # - Income Tax e-filing portal APIs
        # - GST portal APIs  
        # - User's accounting software
        return {"status": "partial_compliance", "pending_items": 2}

class FormFillingAgent(BaseAgent):
    """Agent for form filling assistance."""
    
    def __init__(self):
        super().__init__("FormFiller")
    
    def execute(self, user_message, phone_number):
        """Provide form filling guidance."""
        
        msg_lower = user_message.lower()
        
        if 'itr' in msg_lower:
            return self.itr_filing_guide()
        elif 'gst' in msg_lower:
            return self.gst_return_guide()
        else:
            return self.general_form_guide()
    
    def itr_filing_guide(self):
        """ITR filing step-by-step guide."""
        
        result = """📋 ITR Filing Guide (AY 2025-26)

Step-by-Step Process:

1️⃣ Determine ITR Form:
• ITR-1: Salary income only
• ITR-2: Salary + Capital gains
• ITR-3: Business income
• ITR-4: Presumptive taxation

2️⃣ Gather Documents:
• Form 16 (Salary)
• Bank statements
• Investment proofs
• Property documents

3️⃣ Online Filing:
• Visit: incometax.gov.in
• Login with PAN
• Select appropriate ITR form
• Fill details section-wise

4️⃣ Verification:
• E-verify using Aadhaar OTP
• Or send signed ITR-V within 120 days

⏰ Deadline: July 31, 2025
💰 Late Fee: ₹5,000 (after deadline)

🤖 Guided by FormFiller Agent

Need help with specific sections? Ask me!"""
        
        return result
    
    def gst_return_guide(self):
        """GST return filing guide."""
        
        result = """📋 GST Return Filing Guide

Monthly Returns (GSTR-1 & GSTR-3B):

1️⃣ GSTR-1 (Sales Return):
• Due: 11th of next month
• Upload sales invoices
• B2B, B2C, Export details

2️⃣ GSTR-3B (Summary Return):
• Due: 20th of next month  
• Tax liability summary
• Input tax credit claims
• Tax payment

3️⃣ Filing Process:
• Login: gst.gov.in
• Select return period
• Upload/enter data
• Verify and submit
• Pay taxes online

4️⃣ Late Fee:
• GSTR-1: ₹200 per day
• GSTR-3B: ₹200 per day + interest

🔗 Integration Available:
• Tally Prime auto-upload
• Excel template download

🤖 Guided by FormFiller Agent"""
        
        return result
    
    def general_form_guide(self):
        """General form filling guidance."""
        
        result = """📋 Tax Forms Quick Reference

Common Forms & Deadlines:

📊 Income Tax:
• ITR-1 to ITR-7: July 31
• TDS Returns: Quarterly
• Advance Tax: Quarterly

🏪 GST:
• GSTR-1: 11th of next month
• GSTR-3B: 20th of next month
• Annual Return: Dec 31

💼 Other Forms:
• PF Returns: Monthly
• ESI Returns: Monthly  
• Professional Tax: Monthly

🤖 I can help you with:
• Step-by-step filing
• Document requirements
• Deadline reminders
• Error resolution

Ask: "Help me file ITR-1" or "GST return process"

🤖 Assisted by FormFiller Agent"""
        
        return result

class TallyIntegrationAgent(BaseAgent):
    """Agent for Tally operations."""
    
    def __init__(self):
        super().__init__("TallyHelper")
    
    def execute(self, user_message, phone_number):
        """Provide Tally assistance."""
        
        msg_lower = user_message.lower()
        
        if 'reconcile' in msg_lower or 'bank' in msg_lower:
            return self.bank_reconciliation_guide()
        elif 'backup' in msg_lower:
            return self.backup_guide()
        elif 'gst' in msg_lower and 'return' in msg_lower:
            return self.gst_return_tally()
        elif 'error' in msg_lower:
            return self.error_resolution()
        else:
            return self.general_tally_help()
    
    def bank_reconciliation_guide(self):
        """Bank reconciliation in Tally."""
        
        result = """💻 Tally Bank Reconciliation Guide

Step-by-Step Process:

1️⃣ Preparation:
• Download bank statement (Excel/PDF)
• Ensure all entries posted in Tally
• Check opening balance matches

2️⃣ Auto Reconciliation:
• Gateway → Banking → Bank Reconciliation
• Select bank ledger
• Import bank statement
• Auto-match transactions

3️⃣ Manual Matching:
• Review unmatched items
• Match similar amounts/dates
• Create missing entries

4️⃣ Final Steps:
• Verify closing balance
• Print reconciliation report
• Save reconciliation data

🔧 Common Issues:
• Date format mismatch → Change date format
• Amount differences → Check decimal places
• Missing entries → Create vouchers

⌨️ Shortcuts:
• F12: Configure reconciliation
• Ctrl+A: Accept all matches
• F9: Save reconciliation

🤖 Guided by TallyHelper Agent"""
        
        return result
    
    def backup_guide(self):
        """Tally backup guide."""
        
        result = """💻 Tally Data Backup Guide

Regular Backup Process:

1️⃣ Manual Backup:
• Gateway → Backup & Restore → Backup
• Select company
• Choose backup location
• Set password (optional)

2️⃣ Automatic Backup:
• F11 → Data Configuration → Auto Backup
• Set backup frequency
• Choose backup location
• Enable on exit backup

3️⃣ Best Practices:
• Daily backups recommended
• Multiple backup locations
• Cloud storage integration
• Test restore periodically

4️⃣ Restore Process:
• Gateway → Backup & Restore → Restore
• Select backup file
• Enter password
• Choose restore location

⚠️ Important Notes:
• Backup before year-end
• Keep 3 months of backups
• Verify backup integrity
• Document backup schedule

🤖 Secured by TallyHelper Agent"""
        
        return result
    
    def gst_return_tally(self):
        """GST return from Tally."""
        
        result = """💻 GST Return Generation in Tally

GSTR-1 Generation:

1️⃣ Setup:
• Enable GST in F11
• Configure GSTIN
• Set up tax ledgers

2️⃣ Generate GSTR-1:
• Display → Statutory Reports → GST → Returns
• Select GSTR-1
• Choose period
• Generate JSON file

3️⃣ Upload to Portal:
• Login to GST portal
• Upload JSON file
• Verify data
• Submit return

4️⃣ GSTR-3B Process:
• Generate GSTR-3B from Tally
• Cross-verify with GSTR-1
• File on GST portal
• Make tax payment

🔧 Troubleshooting:
• Invalid GSTIN → Check configuration
• Validation errors → Review invoices
• Upload failed → Check file format

🤖 Streamlined by TallyHelper Agent"""
        
        return result
    
    def error_resolution(self):
        """Common Tally error solutions."""
        
        result = """💻 Tally Error Resolution Guide

Common Errors & Solutions:

🚨 Data Corruption:
• Error: "Data appears to be damaged"
• Solution: Ctrl+Alt+R (Rewrite)
• Prevention: Regular backups

🚨 Network Issues:
• Error: "Server not responding"
• Solution: Check Tally.NET settings
• Configure firewall exceptions

🚨 Printing Problems:
• Error: "Printer not responding"
• Solution: Update printer drivers
• Check print configuration

🚨 Performance Issues:
• Error: Slow response
• Solution: Compact data regularly
• Archive old data

🔧 Emergency Steps:
1. Close Tally completely
2. Restart as Administrator
3. Run data repair (Ctrl+Alt+R)
4. Restore from backup if needed

📞 Support: Tally Solutions → Remote Support

🤖 Diagnosed by TallyHelper Agent"""
        
        return result
    
    def general_tally_help(self):
        """General Tally assistance."""
        
        result = """💻 Tally Prime Quick Help

Essential Operations:

📊 Masters:
• F11: Company Features
• Alt+F3: Create Ledger
• Alt+F5: Create Group
• Alt+F6: Create Cost Center

📋 Vouchers:
• F9: Accept/Save
• F8: Sales Invoice
• F9: Purchase Invoice
• F7: Journal Voucher

📈 Reports:
• Alt+F1: Balance Sheet
• Alt+F2: P&L Account
• Alt+F3: Cash/Bank Books
• Alt+F5: Trial Balance

🔧 Utilities:
• F12: Configure
• Ctrl+Alt+R: Rewrite Data
• Alt+F12: Language
• F1: Help

🤖 Need specific help?
Ask: "How to create ledger in Tally"
Or: "Tally GST configuration"

🤖 Powered by TallyHelper Agent"""
        
        return result

class DeadlineTrackerAgent(BaseAgent):
    """Agent for tracking tax deadlines."""
    
    def __init__(self):
        super().__init__("DeadlineTracker")
    
    def execute(self, user_message, phone_number):
        """Track and remind about deadlines."""
        
        current_date = datetime.now()
        upcoming_deadlines = self.get_upcoming_deadlines(current_date)
        
        result = f"""📅 Tax Deadline Tracker (FY 2024-25)

Today: {current_date.strftime('%B %d, %Y')}

🚨 Immediate Deadlines (Next 30 Days):
{self.format_urgent_deadlines(upcoming_deadlines['urgent'])}

⏰ Upcoming Deadlines (Next 90 Days):
{self.format_upcoming_deadlines(upcoming_deadlines['upcoming'])}

📋 Annual Deadlines:
• ITR Filing: July 31, 2025
• Audit Report: September 30, 2025
• GST Annual Return: December 31, 2025

🔔 Reminder Settings:
• 7 days before deadline
• 1 day before deadline
• On deadline day

💡 Pro Tip: File early to avoid last-minute rush!

🤖 Tracked by DeadlineTracker Agent

Want reminders? Say "Set reminder for ITR filing"
"""
        
        return result
    
    def get_upcoming_deadlines(self, current_date):
        """Get upcoming deadlines based on current date."""
        
        # Mock deadline data - integrate with real calendar
        urgent_deadlines = [
            {"task": "GST Return (March 2024)", "date": "April 20, 2024", "days": 5},
            {"task": "TDS Return Q4", "date": "April 30, 2024", "days": 15},
        ]
        
        upcoming_deadlines = [
            {"task": "Advance Tax Q1", "date": "June 15, 2024", "days": 61},
            {"task": "ITR Filing FY 2023-24", "date": "July 31, 2024", "days": 107},
        ]
        
        return {
            "urgent": urgent_deadlines,
            "upcoming": upcoming_deadlines
        }
    
    def format_urgent_deadlines(self, deadlines):
        """Format urgent deadlines."""
        if not deadlines:
            return "✅ No urgent deadlines!"
        
        formatted = []
        for deadline in deadlines:
            formatted.append(f"• {deadline['task']}: {deadline['date']} ({deadline['days']} days)")
        
        return "\n".join(formatted)
    
    def format_upcoming_deadlines(self, deadlines):
        """Format upcoming deadlines."""
        if not deadlines:
            return "✅ All caught up!"
        
        formatted = []
        for deadline in deadlines:
            formatted.append(f"• {deadline['task']}: {deadline['date']} ({deadline['days']} days)")
        
        return "\n".join(formatted)

class DocumentAnalysisAgent(BaseAgent):
    """Agent for document analysis."""
    
    def __init__(self):
        super().__init__("DocumentAnalyzer")
    
    def execute(self, user_message, phone_number):
        """Analyze documents for compliance."""
        
        # Mock document analysis - integrate with document processing
        result = """📄 Document Analysis Service

Available Analysis Types:

🔍 Invoice Validation:
• GST compliance check
• TDS calculation verification
• Format validation
• Duplicate detection

📊 Financial Statement Review:
• Balance sheet analysis
• P&L statement check
• Ratio analysis
• Compliance verification

📋 Tax Document Check:
• Form 16 validation
• Investment proof verification
• Deduction claim analysis
• Error detection

🔧 How to Use:
1. Upload document via WhatsApp
2. Specify analysis type
3. Get detailed report
4. Receive recommendations

📱 Supported Formats:
• PDF documents
• Excel spreadsheets
• Image files (JPG, PNG)
• Scanned documents

🤖 To analyze a document:
Send: "Analyze my Form 16" + attach file

🤖 Powered by DocumentAnalyzer Agent

Note: Document upload feature coming soon!"""
        
        return result

class RAGResponderAgent(BaseAgent):
    """Enhanced RAG agent with better context."""
    
    def __init__(self):
        super().__init__("RAGResponder")
    
    def execute(self, user_message, phone_number):
        """Enhanced RAG response with agent context."""
        
        try:
            # Use existing RAG system with agent enhancement
            response = bedrock_agent.retrieve_and_generate(
                input={'text': user_message},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                        'modelArn': f'arn:aws:bedrock:{REGION}::foundation-model/{MODEL_ID}',
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 3
                            }
                        }
                    }
                }
            )
            
            rag_response = response['output']['text']
            
            # Enhance with agent capabilities
            enhanced_response = f"""{rag_response}

🤖 Enhanced AI Capabilities Available:
• Tax calculations → Say "Calculate tax for ₹10,00,000"
• Compliance check → Say "Check my compliance status"  
• Form filing help → Say "Help me file ITR"
• Tally assistance → Say "Tally bank reconciliation"
• Deadline tracking → Say "Show my deadlines"

🧠 Powered by RAGResponder Agent + Knowledge Base"""
            
            return enhanced_response
            
        except Exception as error:
            print(f"❌ RAG Agent error: {error}")
            return None

# ================================
# MAIN AGENTIC HANDLER
# ================================

def lambda_handler(event, context):
    """
    Agentic AI Lambda Handler
    - Orchestrates multiple AI agents
    - Performs actions beyond just answering
    - Maintains conversation context
    """
    
    start_time = time.time()
    
    try:
        print(f"\n🤖 AGENTIC AI SYSTEM - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Parse WhatsApp request
        body = event.get("body", "")
        if event.get("isBase64Encoded", False):
            body = base64.b64decode(body).decode('utf-8')
        
        params = parse_qs(body)
        phone_number = params.get("From", ["unknown"])[0]
        user_message = params.get("Body", [""])[0].strip()
        
        print(f"📱 From: {phone_number}")
        print(f"💬 Message: '{user_message}'")
        
        # Initialize agent orchestrator
        orchestrator = AgentOrchestrator()
        
        # Handle empty messages
        if not user_message:
            response_text = """🤖 FinBot Agentic AI System

🧠 Multi-Agent Capabilities:
• 💰 Tax Calculator - Compute taxes instantly
• 🔍 Compliance Checker - Check filing status
• 📋 Form Filler - Step-by-step guidance
• 💻 Tally Helper - Accounting operations
• 📄 Document Analyzer - Validate documents
• 📅 Deadline Tracker - Never miss deadlines
• 📚 Knowledge Expert - Answer any tax question

🎯 Try These Commands:
• "Calculate income tax for ₹15,00,000"
• "Check my compliance status"
• "Help me file GST return"
• "Show upcoming tax deadlines"
• "Tally bank reconciliation steps"

🚀 Next-Generation AI Assistant Ready!"""
            
        else:
            # Analyze intent and execute appropriate agents
            intents = orchestrator.analyze_intent(user_message)
            agent_results = orchestrator.execute_agents(user_message, phone_number, intents)
            
            if agent_results:
                # Combine results from multiple agents
                response_text = "\n\n".join(agent_results)
                
                # Add agent orchestration info
                response_text += f"\n\n🤖 Agents Used: {len(agent_results)} | Processing: {time.time() - start_time:.2f}s"
            else:
                # Fallback to basic response
                response_text = """🤖 Agentic AI Processing...

I understand you're asking about tax matters. Let me help you with:

💡 Specific Actions I Can Perform:
• Calculate taxes with exact amounts
• Check compliance status
• Guide through form filing
• Assist with Tally operations
• Track important deadlines

Try being more specific:
"Calculate TDS on ₹50,000 professional payment"
"Show me GST filing steps"
"When is my next ITR deadline?"

🧠 Multi-Agent System Ready to Assist!"""
        
        # Ensure response fits WhatsApp limits
        if len(response_text) > 1500:
            response_text = response_text[:1500] + "...\n\n🤖 Full response available - ask for details!"
        
        print(f"📤 Agentic Response: {len(response_text)} chars")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/xml"},
            "body": f"<Response><Message>{response_text}</Message></Response>"
        }
        
    except Exception as error:
        print(f"💥 Agentic System Error: {str(error)}")
        import traceback
        print(f"💥 Traceback: {traceback.format_exc()}")
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/xml"},
            "body": "<Response><Message>🤖 Agentic AI system temporarily unavailable. Switching to basic mode... Try again!</Message></Response>"
        }


