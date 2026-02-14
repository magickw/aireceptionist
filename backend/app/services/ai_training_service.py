"""
AI Training Service - Manage and test training scenarios
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import AITrainingScenario, Business
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
            
            # Calculate similarity (simple word overlap for now)
            similarity = self._calculate_similarity(
                ai_response, 
                scenario.expected_response
            )
            
            # Update scenario stats
            scenario.last_tested = datetime.utcnow()
            scenario.success_rate = similarity
            
            # Update success rate based on threshold
            if similarity >= 70:  # 70% threshold
                scenario.success_rate = min(100, similarity + 5)  # Bonus for success
            else:
                scenario.success_rate = max(0, similarity - 10)  # Penalty for failure
            
            db.commit()
            
            return {
                "scenario_id": scenario_id,
                "user_input": scenario.user_input,
                "expected_response": scenario.expected_response,
                "ai_response": ai_response,
                "similarity_score": similarity,
                "passed": similarity >= 70,
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
        
        for scenario in scenarios:
            result = await self.test_scenario(
                db, 
                scenario.id, 
                business_id,
                business_context
            )
            
            if "error" not in result:
                results.append(result)
                if result["passed"]:
                    passed += 1
                else:
                    failed += 1
        
        return {
            "total": len(scenarios),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(scenarios) * 100) if scenarios else 0,
            "results": results
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple similarity score between two texts
        Using word overlap approach
        """
        
        # Normalize text
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        jaccard = len(intersection) / len(union)
        
        # Convert to percentage
        return round(jaccard * 100, 2)
    
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


# Singleton instance
ai_training_service = AITrainingService()
