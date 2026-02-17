"""
AI Training Service - Manage and test training scenarios
"""

from app.models.models import AITrainingScenario, Business, TrainingSnapshot, BenchmarkResult
from app.services.nova_reasoning import nova_reasoning


class AITrainingService:
    """Service for managing AI training scenarios"""
    
    CATEGORIES = [
        "appointment_booking",
        "customer_support", 
        "sales_inquiry",
        "general_inquiry",
        "complaint_handling",
        "information_request"
    ]
    
    async def create_scenario(
        self,
        db: Session,
        business_id: int,
        title: str,
        user_input: str,
        expected_response: str,
        description: Optional[str] = None,
        category: Optional[str] = "general_inquiry"
    ) -> AITrainingScenario:
        """Create a new training scenario"""
        
        scenario = AITrainingScenario(
            business_id=business_id,
            title=title,
            description=description,
            category=category,
            user_input=user_input,
            expected_response=expected_response,
            is_active=True
        )
        
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        
        return scenario
    
    async def list_scenarios(
        self,
        db: Session,
        business_id: int,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[AITrainingScenario]:
        """List all training scenarios for a business"""
        
        query = db.query(AITrainingScenario).filter(
            AITrainingScenario.business_id == business_id
        )
        
        if category:
            query = query.filter(AITrainingScenario.category == category)
        
        if is_active is not None:
            query = query.filter(AITrainingScenario.is_active == is_active)
        
        return query.order_by(AITrainingScenario.created_at.desc()).all()
    
    async def get_scenario(
        self,
        db: Session,
        scenario_id: int,
        business_id: int
    ) -> Optional[AITrainingScenario]:
        """Get a specific training scenario"""
        
        return db.query(AITrainingScenario).filter(
            AITrainingScenario.id == scenario_id,
            AITrainingScenario.business_id == business_id
        ).first()
    
    async def update_scenario(
        self,
        db: Session,
        scenario_id: int,
        business_id: int,
        **kwargs
    ) -> Optional[AITrainingScenario]:
        """Update a training scenario"""
        
        scenario = await self.get_scenario(db, scenario_id, business_id)
        
        if not scenario:
            return None
        
        for key, value in kwargs.items():
            if hasattr(scenario, key) and value is not None:
                setattr(scenario, key, value)
        
        db.commit()
        db.refresh(scenario)
        
        return scenario
    
    async def delete_scenario(
        self,
        db: Session,
        scenario_id: int,
        business_id: int
    ) -> bool:
        """Delete a training scenario"""
        
        scenario = await self.get_scenario(db, scenario_id, business_id)
        
        if not scenario:
            return False
        
        db.delete(scenario)
        db.commit()
        
        return True
    
    async def test_scenario(
        self,
        db: Session,
        scenario_id: int,
        business_id: int,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test a training scenario by running it through Nova AI
        and comparing the response with expected output
        """
        
        scenario = await self.get_scenario(db, scenario_id, business_id)
        
        if not scenario:
            return {"error": "Scenario not found"}
        
        # Get AI response using Nova reasoning
        try:
            result = await nova_reasoning.reason(
                conversation=scenario.user_input,
                business_context=business_context,
                customer_context={}
            )
            
            ai_response = result.get("suggested_response", "")
            
            # Calculate similarity using LLM-as-a-Judge for semantic meaning
            similarity = await nova_reasoning.evaluate_response_quality(
                user_input=scenario.user_input,
                expected_response=scenario.expected_response,
                actual_response=ai_response
            )
            
            # Update scenario stats
            scenario.last_tested = datetime.utcnow()
            scenario.success_rate = similarity
            
            db.commit()
            
            return {
                "scenario_id": scenario_id,
                "user_input": scenario.user_input,
                "expected_response": scenario.expected_response,
                "ai_response": ai_response,
                "similarity_score": similarity,
                "passed": similarity >= 70,
                "intent": result.get("intent"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "scenario_id": scenario_id
            }
    
    async def test_all_scenarios(
        self,
        db: Session,
        business_id: int,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test all active scenarios for a business"""
        
        scenarios = await self.list_scenarios(
            db, 
            business_id, 
            is_active=True
        )
        
        results = []
        passed = 0
        failed = 0
        total_score = 0
        
        for scenario in scenarios:
            result = await self.test_scenario(
                db, 
                scenario.id, 
                business_id,
                business_context
            )
            
            if "error" not in result:
                results.append(result)
                total_score += result["similarity_score"]
                if result["passed"]:
                    passed += 1
                else:
                    failed += 1
        
        avg_score = (total_score / len(scenarios)) if scenarios else 0
        
        # Save benchmark result
        benchmark = BenchmarkResult(
            business_id=business_id,
            total_scenarios=len(scenarios),
            passed_scenarios=passed,
            avg_score=avg_score,
            detailed_results=results
        )
        db.add(benchmark)
        db.commit()
        
        return {
            "total": len(scenarios),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(scenarios) * 100) if scenarios else 0,
            "avg_score": round(avg_score, 2),
            "results": results
        }
    
    async def create_snapshot(
        self,
        db: Session,
        business_id: int,
        name: str,
        description: Optional[str] = None
    ) -> TrainingSnapshot:
        """Create a versioned snapshot of current training data"""
        
        scenarios = await self.list_scenarios(db, business_id, is_active=True)
        
        # Get latest version number
        latest = db.query(TrainingSnapshot).filter(
            TrainingSnapshot.business_id == business_id
        ).order_by(TrainingSnapshot.version.desc()).first()
        
        version = (latest.version + 1) if latest else 1
        
        # Calculate current success rate
        avg_rate = sum([float(s.success_rate or 0) for s in scenarios]) / len(scenarios) if scenarios else 0
        
        snapshot = TrainingSnapshot(
            business_id=business_id,
            version=version,
            name=name,
            description=description,
            scenario_count=len(scenarios),
            avg_success_rate=avg_rate,
            scenario_data=[{
                "id": s.id,
                "user_input": s.user_input,
                "expected_response": s.expected_response,
                "category": s.category
            } for s in scenarios]
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        
        return snapshot

    async def list_snapshots(
        self,
        db: Session,
        business_id: int
    ) -> List[TrainingSnapshot]:
        """List all snapshots for a business"""
        return db.query(TrainingSnapshot).filter(
            TrainingSnapshot.business_id == business_id
        ).order_by(TrainingSnapshot.version.desc()).all()

    async def get_benchmarks(
        self,
        db: Session,
        business_id: int,
        limit: int = 10
    ) -> List[BenchmarkResult]:
        """Get recent benchmark results"""
        return db.query(BenchmarkResult).filter(
            BenchmarkResult.business_id == business_id
        ).order_by(BenchmarkResult.created_at.desc()).limit(limit).all()

    async def generate_synthetic_scenarios(
        self,
        db: Session,
        business_id: int,
        count: int = 5
    ) -> List[AITrainingScenario]:
        """Generate and save synthetic training scenarios"""
        
        # Get business context
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return []
            
        services = business.settings.get("services", []) if business.settings else []
        
        # Generate data using Nova
        synthetic_data = await nova_reasoning.generate_synthetic_training_data(
            business_type=business.type,
            services=services,
            count=count
        )
        
        created_scenarios = []
        for item in synthetic_data:
            scenario = await self.create_scenario(
                db=db,
                business_id=business_id,
                title=f"Auto-Generated: {item.get('user_input', '')[:30]}...",
                user_input=item.get("user_input", ""),
                expected_response=item.get("expected_response", ""),
                category=item.get("category", "general_inquiry"),
                description="Generated by Nova AI"
            )
            created_scenarios.append(scenario)
            
        return created_scenarios

    async def get_statistics(
        self,
        db: Session,
        business_id: int
    ) -> Dict[str, Any]:
        """Get training statistics for a business"""
        
        scenarios = await self.list_scenarios(db, business_id)
        
        if not scenarios:
            return {
                "total_scenarios": 0,
                "active_scenarios": 0,
                "average_success_rate": 0,
                "by_category": {}
            }
        
        active = [s for s in scenarios if s.is_active]
        
        # Calculate averages
        success_rates = [
            float(s.success_rate) 
            for s in scenarios 
            if s.success_rate is not None
        ]
        
        avg_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        
        # Group by category
        by_category = {}
        for category in self.CATEGORIES:
            cat_scenarios = [s for s in scenarios if s.category == category]
            if cat_scenarios:
                cat_rates = [
                    float(s.success_rate) 
                    for s in cat_scenarios 
                    if s.success_rate is not None
                ]
                by_category[category] = {
                    "count": len(cat_scenarios),
                    "avg_success": sum(cat_rates) / len(cat_rates) if cat_rates else 0
                }
        
        return {
            "total_scenarios": len(scenarios),
            "active_scenarios": len(active),
            "average_success_rate": round(avg_rate, 2),
            "by_category": by_category,
            "untested": len([s for s in scenarios if s.success_rate is None])
        }

    async def create_scenario_from_approval(
        self,
        db: Session,
        business_id: int,
        approval_id: int
    ) -> Optional[AITrainingScenario]:
        """Create a training scenario from a reviewed approval request"""
        from app.models.models import ApprovalRequest
        
        approval = db.query(ApprovalRequest).filter(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.business_id == business_id
        ).first()
        
        if not approval or not approval.final_response:
            return None
        
        # Get the original user input from the context
        # In the context, we usually store the last user message or the whole conversation
        context = approval.context or {}
        user_input = context.get("user_input") or context.get("conversation")
        
        # If context doesn't have it, we might need to look up the last message in the session
        if not user_input and approval.call_session_id:
            from app.models.models import ConversationMessage
            last_msg = db.query(ConversationMessage).filter(
                ConversationMessage.call_session_id == approval.call_session_id,
                ConversationMessage.sender == "customer"
            ).order_by(ConversationMessage.timestamp.desc()).first()
            
            if last_msg:
                user_input = last_msg.content
        
        if not user_input:
            user_input = "Unknown customer query"
            
        return await self.create_scenario(
            db=db,
            business_id=business_id,
            title=f"Feedback from Approval #{approval_id}",
            user_input=user_input,
            expected_response=approval.final_response,
            description=f"Automatically created from manager review: {approval.reason}",
            category="complaint_handling" if approval.request_type == "HUMAN_INTERVENTION" else "general_inquiry"
        )

    async def create_scenario_from_call_log(
        self,
        db: Session,
        business_id: int,
        call_session_id: str,
        user_input: str,
        expected_response: str,
        category: str = "general_inquiry"
    ) -> AITrainingScenario:
        """Create a training scenario from a manual correction in a call log"""
        
        return await self.create_scenario(
            db=db,
            business_id=business_id,
            title=f"Correction for Call Session {call_session_id[:8]}",
            user_input=user_input,
            expected_response=expected_response,
            description=f"Manually added from call log history: {call_session_id}",
            category=category
        )


# Singleton instance
ai_training_service = AITrainingService()
